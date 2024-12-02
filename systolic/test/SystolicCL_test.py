"""
==========================================================================
SystolicCL_test.py
==========================================================================
Test cases for Systolic Array with CL data/config memory.

Author : Cheng Tan
  Date : Dec 28, 2019
"""


from pymtl3 import *
from ..SystolicCL import SystolicCL
from ...fu.double.SeqMulAdderRTL import SeqMulAdderRTL
from ...fu.flexible.FlexibleFuRTL import FlexibleFuRTL
from ...fu.single.AdderRTL import AdderRTL
from ...fu.single.MemUnitRTL import MemUnitRTL
from ...lib.basic.en_rdy.test_sinks import TestSinkRTL
from ...lib.basic.en_rdy.test_srcs import TestSrcRTL
from ...lib.messages import *
from ...lib.opt_type import *
from ...lib.util.ctrl_helper import *
import os


kMaxCycles = 6

#-------------------------------------------------------------------------
# Test harness
#-------------------------------------------------------------------------

class TestHarness( Component ):

  def construct( s, DUT, FunctionUnit, FuList, DataType, PredicateType,
                 CtrlType, width, height, ctrl_mem_size, data_mem_size,
                 src_opt, preload_data, preload_const, sink_out ):

    s.num_tiles = width * height
    AddrType = mk_bits( clog2( ctrl_mem_size ) )

    s.sink_out  = [ TestSinkRTL( DataType, sink_out[i] )
                  for i in range( height-1 ) ]

    s.dut = DUT( FunctionUnit, FuList, DataType, PredicateType, CtrlType,
                 width, height, ctrl_mem_size, data_mem_size,
                 len( src_opt[0] ), kMaxCycles, src_opt,
                 preload_data, preload_const )

    for i in range( height-1 ):
      connect( s.dut.send_data[i],  s.sink_out[i].recv )

  def line_trace( s ):
    return s.dut.line_trace()

def run_sim( test_harness, max_cycles = kMaxCycles ):
  test_harness.elaborate()
  test_harness.apply( DefaultPassGroup() )

  # Run simulation
  ncycles = 0
  print()
  print( "{}:{}".format( ncycles, test_harness.line_trace() ))
  while ncycles < max_cycles:
    test_harness.sim_tick()
    ncycles += 1
    print( "----------------------------------------------------" )
    print( "{}:{}".format( ncycles, test_harness.line_trace() ))

  # Check timeout
#  assert ncycles < max_cycles

  test_harness.sim_tick()
  test_harness.sim_tick()
  test_harness.sim_tick()

# ------------------------------------------------------------------
# To emulate systolic array
# left bottom is 0, 0
# right top   is 1, 1
# 1: North, 2: South, 3: West, 4: East
# 5 - 8: registers
# ------------------------------------------------------------------
def test_systolic_2x2():
  num_tile_inports  = 4
  num_tile_outports = 4
  num_xbar_inports  = 6
  num_xbar_outports = 8
  ctrl_mem_size     = 8
  width             = 2
  height            = 3
  RouteType         = mk_bits( clog2( num_xbar_inports + 1 ) )
  AddrType          = mk_bits( clog2( ctrl_mem_size ) )
  num_tiles         = width * height
  ctrl_mem_size     = 8
  data_mem_size     = 2
  # number of inputs of FU is fixed inside the tile
  num_fu_in         = 4

  DUT               = SystolicCL
  FunctionUnit      = FlexibleFuRTL
  FuList            = [AdderRTL, MemUnitRTL, SeqMulAdderRTL]
  DataType          = mk_data( 16, 1 )
  PredicateType     = mk_predicate( 1, 1 )
  CtrlType          = mk_ctrl( num_fu_in, num_xbar_inports, num_xbar_outports )
  FuInType          = mk_bits( clog2( num_fu_in + 1 ) )
  pickRegister      = [ FuInType( x+1 ) for x in range( num_fu_in ) ]

  src_opt       = [
                   # Tile 0:
                   [CtrlType( OPT_LD_CONST, b1( 0 ), pickRegister, [
                    RouteType(5), RouteType(0), RouteType(0), RouteType(0),
                    RouteType(0), RouteType(0), RouteType(0), RouteType(0)] ),
                    CtrlType( OPT_LD_CONST, b1( 0 ), pickRegister, [
                    RouteType(5), RouteType(0), RouteType(0), RouteType(0),
                    RouteType(0), RouteType(0), RouteType(0), RouteType(0)] ),
                    CtrlType( OPT_LD_CONST, b1( 0 ), pickRegister, [
                    RouteType(5), RouteType(0), RouteType(0), RouteType(0),
                    RouteType(0), RouteType(0), RouteType(0), RouteType(0)] ),
                    CtrlType( OPT_LD_CONST, b1( 0 ), pickRegister, [
                    RouteType(5), RouteType(0), RouteType(0), RouteType(0),
                    RouteType(0), RouteType(0), RouteType(0), RouteType(0)] ),
                   ],
                   # Tile 1:
                   [CtrlType( OPT_NAH, b1( 0 ), pickRegister, [
                    RouteType(5), RouteType(0), RouteType(0), RouteType(0),
                    RouteType(0), RouteType(0), RouteType(0), RouteType(0)] ),
                    CtrlType( OPT_LD_CONST, b1( 0 ), pickRegister, [
                    RouteType(5), RouteType(0), RouteType(0), RouteType(0),
                    RouteType(0), RouteType(0), RouteType(0), RouteType(0)] ),
                    CtrlType( OPT_LD_CONST, b1( 0 ), pickRegister, [
                    RouteType(5), RouteType(0), RouteType(0), RouteType(0),
                    RouteType(0), RouteType(0), RouteType(0), RouteType(0)] ),
                    CtrlType( OPT_LD_CONST, b1( 0 ), pickRegister, [
                    RouteType(5), RouteType(0), RouteType(0), RouteType(0),
                    RouteType(0), RouteType(0), RouteType(0), RouteType(0)] ),
                    CtrlType( OPT_LD_CONST, b1( 0 ), pickRegister, [
                    RouteType(5), RouteType(0), RouteType(0), RouteType(0),
                    RouteType(0), RouteType(0), RouteType(0), RouteType(0)] ),
                   ],
                   # Tile 2:
                   [CtrlType( OPT_NAH, b1( 0 ), pickRegister, [
                    RouteType(2), RouteType(0), RouteType(0), RouteType(0),
                    RouteType(2), RouteType(0), RouteType(0), RouteType(0)] ),
                    CtrlType( OPT_MUL_CONST, b1( 0 ), pickRegister, [
                    RouteType(2), RouteType(0), RouteType(0), RouteType(5),
                    RouteType(2), RouteType(0), RouteType(0), RouteType(0)] ),
                    CtrlType( OPT_MUL_CONST, b1( 0 ), pickRegister, [
                    RouteType(2), RouteType(0), RouteType(0), RouteType(5),
                    RouteType(2), RouteType(0), RouteType(0), RouteType(0)] ),
                    CtrlType( OPT_MUL_CONST, b1( 0 ), pickRegister, [
                    RouteType(2), RouteType(0), RouteType(0), RouteType(5),
                    RouteType(2), RouteType(0), RouteType(0), RouteType(0)] ),
                   ],
                   # Tile 3:
                   [CtrlType( OPT_NAH, b1( 0 ), pickRegister, [
                    RouteType(2), RouteType(0), RouteType(0), RouteType(0),
                    RouteType(2), RouteType(0), RouteType(0), RouteType(0)] ),
                    CtrlType( OPT_NAH, b1( 0 ), pickRegister, [
                    RouteType(2), RouteType(0), RouteType(0), RouteType(0),
                    RouteType(2), RouteType(0), RouteType(3), RouteType(0)] ),
                    CtrlType( OPT_MUL_CONST_ADD, b1( 0 ), pickRegister, [
                    RouteType(2), RouteType(0), RouteType(0), RouteType(5),
                    RouteType(2), RouteType(0), RouteType(3), RouteType(0)] ),
                    CtrlType( OPT_MUL_CONST_ADD, b1( 0 ), pickRegister, [
                    RouteType(2), RouteType(0), RouteType(0), RouteType(5),
                    RouteType(2), RouteType(0), RouteType(3), RouteType(0)] ),
                   ],
                   # Tile 4:
                   [CtrlType( OPT_NAH, b1( 0 ), pickRegister, [
                    RouteType(0), RouteType(0), RouteType(0), RouteType(0),
                    RouteType(2), RouteType(0), RouteType(0), RouteType(0)] ),
                    CtrlType( OPT_NAH, b1( 0 ), pickRegister, [
                    RouteType(0), RouteType(0), RouteType(0), RouteType(0),
                    RouteType(2), RouteType(0), RouteType(0), RouteType(0)] ),
                    CtrlType( OPT_MUL_CONST, b1( 0 ), pickRegister, [
                    RouteType(0), RouteType(0), RouteType(0), RouteType(5),
                    RouteType(2), RouteType(0), RouteType(0), RouteType(0)] ),
                    CtrlType( OPT_MUL_CONST, b1( 0 ), pickRegister, [
                    RouteType(0), RouteType(0), RouteType(0), RouteType(5),
                    RouteType(2), RouteType(0), RouteType(0), RouteType(0)] ),
                   ],
                   # Tile 5:
                   [CtrlType( OPT_NAH, b1( 0 ), pickRegister, [
                    RouteType(0), RouteType(0), RouteType(0), RouteType(0),
                    RouteType(2), RouteType(0), RouteType(3), RouteType(0)] ),
                    CtrlType( OPT_NAH, b1( 0 ), pickRegister, [
                    RouteType(0), RouteType(0), RouteType(0), RouteType(0),
                    RouteType(2), RouteType(0), RouteType(3), RouteType(0)] ),
                    CtrlType( OPT_NAH, b1( 0 ), pickRegister, [
                    RouteType(0), RouteType(0), RouteType(0), RouteType(0),
                    RouteType(2), RouteType(0), RouteType(3), RouteType(0)] ),
                    CtrlType( OPT_MUL_CONST_ADD, b1( 0 ), pickRegister, [
                    RouteType(0), RouteType(0), RouteType(0), RouteType(5),
                    RouteType(2), RouteType(0), RouteType(3), RouteType(0)] ),
                    CtrlType( OPT_MUL_CONST_ADD, b1( 0 ), pickRegister, [
                    RouteType(0), RouteType(0), RouteType(0), RouteType(5),
                    RouteType(2), RouteType(0), RouteType(3), RouteType(0)] ),
                   ]
                  ]
  preload_mem   = [DataType(1, 1), DataType(2, 1), DataType(3, 1), DataType(4, 1)]
  preload_const = [[DataType(0, 1), DataType(1, 1)],
                   [DataType(0, 0), DataType(2, 1), DataType(3, 1)], # offset address used for loading
                   [DataType(2, 1)], [DataType(4, 1)], # preloaded data
                   [DataType(6, 1)], [DataType(8, 1)]] # preloaded data
  """
  1 3      2 6     14 20
       x        =
  2 4      4 8     30 44
  """
  sink_out = [[DataType(14, 1), DataType(20, 1)], [DataType(30, 1), DataType(44, 1)]]
  th = TestHarness( DUT, FunctionUnit, FuList, DataType, PredicateType,
                    CtrlType, width, height, ctrl_mem_size, len(preload_mem),
                    src_opt, preload_mem, preload_const, sink_out )
  run_sim( th )


