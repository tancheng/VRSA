"""
==========================================================================
Phi_test.py
==========================================================================
Test cases for functional unit Phi.

Author : Cheng Tan
  Date : November 27, 2019
"""


from pymtl3 import *
from ..RegFile import RegFile
from ...lib.basic.en_rdy.test_sinks import TestSinkRTL
from ...lib.basic.en_rdy.test_srcs import TestSrcRTL
from ...lib.messages import *
from ...lib.opt_type import *


#-------------------------------------------------------------------------
# Test harness
#-------------------------------------------------------------------------

class TestHarness( Component ):

  def construct( s, FunctionUnit, DataType, nregs,
                 src_waddr, src_wdata, src_raddr, sink_rdata ):

    AddrType = mk_bits( max(clog2( nregs ), 1) )

    s.src_waddr  = TestSrcRTL ( AddrType, src_waddr  )
    s.src_wdata  = TestSrcRTL ( DataType, src_wdata  )
    s.src_raddr  = TestSrcRTL ( AddrType, src_raddr  )
    s.sink_rdata = TestSinkRTL( DataType, sink_rdata )

    s.dut = FunctionUnit( DataType, nregs )

    connect( s.src_waddr.send,   s.dut.recv_waddr  )
    connect( s.src_wdata.send,   s.dut.recv_wdata  )
    connect( s.src_raddr.send,   s.dut.recv_raddr  )
    connect( s.dut.send_rdata,   s.sink_rdata.recv )

  def done( s ):
    return s.src_waddr.done() and s.src_raddr.done()

  def line_trace( s ):
    return s.dut.line_trace()

def run_sim( test_harness, max_cycles=100 ):
  test_harness.elaborate()
  test_harness.apply( DefaultPassGroup() )
  test_harness.sim_reset()

  # Run simulation

  ncycles = 0
  print()
  print( "{}:{}".format( ncycles, test_harness.line_trace() ))
  while not test_harness.done() and ncycles < max_cycles:
    test_harness.sim_tick()
    ncycles += 1
    print( "{}:{}".format( ncycles, test_harness.line_trace() ))

  # Check timeout

  assert ncycles < max_cycles

  print( "{}:{}".format( ncycles, test_harness.line_trace() ))

  test_harness.sim_tick()
  test_harness.sim_tick()
  test_harness.sim_tick()

def test_RegFile():
  FU = RegFile
#  DataType  = mk_data( 16, 1 )
  nregs      = 1
  DataType   = Bits32
  AddrType   = mk_bits( max(clog2( nregs ), 1) )
  src_waddr  = [ AddrType(0), AddrType(0), AddrType(0) ]
  src_wdata  = [ DataType(1), DataType(3), DataType(2) ]
  src_raddr  = [ AddrType(0), AddrType(0), AddrType(0) ]
  sink_rdata = [ DataType(0), DataType(1), DataType(3), DataType(2) ]
  th = TestHarness( FU, DataType, nregs, src_waddr, src_wdata,
                    src_raddr, sink_rdata )
  run_sim( th )
