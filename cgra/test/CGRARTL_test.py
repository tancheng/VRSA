"""
==========================================================================
CGRARTL_test.py
==========================================================================
Test cases for CGRAs with different configurations.

Author : Cheng Tan
  Date : Dec 15, 2019
"""


from pymtl3 import *
from pymtl3.stdlib.test_utils import (run_sim,
                                      config_model_with_cmdline_opts)
from pymtl3.passes.backends.verilog import (VerilogTranslationPass,
                                            VerilogVerilatorImportPass)
from ..CGRARTL import CGRARTL
from ...lib.basic.en_rdy.test_srcs import TestSrcRTL
from ...lib.messages import *
from ...lib.opt_type import *
from ...fu.flexible.FlexibleFuRTL import FlexibleFuRTL
from ...fu.single.AdderRTL import AdderRTL
from ...fu.single.MemUnitRTL import MemUnitRTL
from ...fu.single.ShifterRTL import ShifterRTL


#-------------------------------------------------------------------------
# Test harness
#-------------------------------------------------------------------------

class TestHarness( Component ):

  def construct( s, DUT, FunctionUnit, FuList, DataType, PredicateType,
                 CtrlType, width, height, ctrl_mem_size, data_mem_size,
                 src_opt, ctrl_waddr):

    s.num_tiles = width * height
    AddrType = mk_bits( clog2( ctrl_mem_size ) )

    s.src_opt     = [ TestSrcRTL( CtrlType, src_opt[i] )
                      for i in range( s.num_tiles ) ]
    s.ctrl_waddr  = [ TestSrcRTL( AddrType, ctrl_waddr[i] )
                      for i in range( s.num_tiles ) ]

    s.dut = DUT( DataType, PredicateType, CtrlType, width, height,
                 ctrl_mem_size, data_mem_size, len( src_opt[0] ),
                 len( src_opt[0] ), FunctionUnit, FuList )

    for i in range( s.num_tiles ):
      connect( s.src_opt[i].send,     s.dut.recv_wopt[i]  )
      connect( s.ctrl_waddr[i].send,  s.dut.recv_waddr[i] )

  def done( s ):
    done = True
    for i in range( s.num_tiles  ):
      if not s.src_opt[i].done():
        done = False
        break
    return done

  def line_trace( s ):
    return s.dut.line_trace()

def test_homo_2x2( cmdline_opts ):
  num_tile_inports  = 4
  num_tile_outports = 4
  num_xbar_inports  = 6
  num_xbar_outports = 8
  ctrl_mem_size     = 6
  width         = 2
  height        = 2
  RouteType     = mk_bits( clog2( num_xbar_inports + 1 ) )
  AddrType      = mk_bits( clog2( ctrl_mem_size ) )
  num_tiles     = width * height
  data_mem_size = 8
  num_fu_in     = 4
  DUT           = CGRARTL
  FunctionUnit  = FlexibleFuRTL
  FuList        = [MemUnitRTL, AdderRTL]
  DataType      = mk_data( 16, 1 )
  PredicateType = mk_predicate( 1, 1 )
  CtrlType      = mk_ctrl( num_fu_in, num_xbar_inports, num_xbar_outports )
  FuInType      = mk_bits( clog2( num_fu_in + 1 ) )
  pickRegister  = [ FuInType( x+1 ) for x in range( num_fu_in ) ]
  src_opt       = [[ CtrlType( OPT_INC, b1( 0 ), pickRegister, [
                     RouteType(4), RouteType(3), RouteType(2), RouteType(1),
                     RouteType(5), RouteType(5), RouteType(5), RouteType(5)] ),
                     CtrlType( OPT_INC, b1( 0 ), pickRegister, [
                     RouteType(4),RouteType(3), RouteType(2), RouteType(1),
                     RouteType(5), RouteType(5), RouteType(5), RouteType(5)] ),
                     CtrlType( OPT_ADD, b1( 0 ), pickRegister, [
                     RouteType(4),RouteType(3), RouteType(2), RouteType(1),
                     RouteType(5), RouteType(5), RouteType(5), RouteType(5)] ),
                     CtrlType( OPT_STR, b1( 0 ), pickRegister, [
                     RouteType(4),RouteType(3), RouteType(2), RouteType(1),
                     RouteType(5), RouteType(5), RouteType(5), RouteType(5)] ),
                     CtrlType( OPT_ADD, b1( 0 ), pickRegister, [
                     RouteType(4),RouteType(3), RouteType(2), RouteType(1),
                     RouteType(5), RouteType(5), RouteType(5), RouteType(5)] ),
                     CtrlType( OPT_ADD, b1( 0 ), pickRegister, [
                     RouteType(4),RouteType(3), RouteType(2), RouteType(1),
                     RouteType(5), RouteType(5), RouteType(5), RouteType(5)] ) ]
                     for _ in range( num_tiles ) ]
  ctrl_waddr   = [[ AddrType( 0 ), AddrType( 1 ), AddrType( 2 ), AddrType( 3 ),
                    AddrType( 4 ), AddrType( 5 ) ] for _ in range( num_tiles ) ]
  th = TestHarness( DUT, FunctionUnit, FuList, DataType, PredicateType,
                    CtrlType, width, height, ctrl_mem_size, data_mem_size,
                    src_opt, ctrl_waddr )
  th.elaborate()
  th.dut.set_metadata( VerilogVerilatorImportPass.vl_Wno_list,
                    ['UNSIGNED', 'UNOPTFLAT', 'WIDTH', 'WIDTHCONCAT',
                     'ALWCOMBORDER'] )
  th = config_model_with_cmdline_opts( th, cmdline_opts, duts=['dut'] )
  run_sim( th )

def test_hetero_2x2( cmdline_opts ):
  num_tile_inports  = 4
  num_tile_outports = 4
  num_xbar_inports  = 6
  num_xbar_outports = 8
  ctrl_mem_size     = 6
  width             = 2
  height            = 2
  RouteType         = mk_bits( clog2( num_xbar_inports + 1 ) )
  AddrType          = mk_bits( clog2( ctrl_mem_size ) )
  num_tiles         = width * height
  data_mem_size     = 8
  num_fu_in         = 4
  DUT               = CGRARTL
  FunctionUnit      = FlexibleFuRTL
  FuList            = [MemUnitRTL, AdderRTL]
  DataType          = mk_data( 16, 1 )
  PredicateType     = mk_predicate( 1, 1 )
  CtrlType          = mk_ctrl( num_fu_in, num_xbar_inports, num_xbar_outports )
  FuInType          = mk_bits( clog2( num_fu_in + 1 ) )
  pickRegister      = [ FuInType( x+1 ) for x in range( num_fu_in ) ]
  src_opt           = [[ CtrlType( OPT_INC, b1( 0 ), pickRegister, [
                         RouteType(4), RouteType(3), RouteType(2), RouteType(1),
                         RouteType(5), RouteType(5), RouteType(5), RouteType(5)] ),
                         CtrlType( OPT_INC, b1( 0 ), pickRegister, [
                         RouteType(4),RouteType(3), RouteType(2), RouteType(1),
                         RouteType(5), RouteType(5), RouteType(5), RouteType(5)] ),
                         CtrlType( OPT_ADD, b1( 0 ), pickRegister, [
                         RouteType(4),RouteType(3), RouteType(2), RouteType(1),
                         RouteType(5), RouteType(5), RouteType(5), RouteType(5)] ),
                         CtrlType( OPT_STR, b1( 0 ), pickRegister, [
                         RouteType(4),RouteType(3), RouteType(2), RouteType(1),
                         RouteType(5), RouteType(5), RouteType(5), RouteType(5)] ),
                         CtrlType( OPT_ADD, b1( 0 ), pickRegister, [
                         RouteType(4),RouteType(3), RouteType(2), RouteType(1),
                         RouteType(5), RouteType(5), RouteType(5), RouteType(5)] ),
                         CtrlType( OPT_ADD, b1( 0 ), pickRegister, [
                         RouteType(4),RouteType(3), RouteType(2), RouteType(1),
                         RouteType(5), RouteType(5), RouteType(5), RouteType(5)] ) ]
                         for _ in range( num_tiles ) ]
  ctrl_waddr        = [[ AddrType( 0 ), AddrType( 1 ), AddrType( 2 ), AddrType( 3 ),
                         AddrType( 4 ), AddrType( 5 ) ] for _ in range( num_tiles ) ]
  th = TestHarness( DUT, FunctionUnit, FuList, DataType, PredicateType,
                    CtrlType, width, height, ctrl_mem_size, data_mem_size,
                    src_opt, ctrl_waddr )
  th.set_param("top.dut.tile[1].construct", FuList=[ShifterRTL])
  th.elaborate()
  th.dut.set_metadata( VerilogVerilatorImportPass.vl_Wno_list,
                    ['UNSIGNED', 'UNOPTFLAT', 'WIDTH', 'WIDTHCONCAT',
                     'ALWCOMBORDER'] )
  th = config_model_with_cmdline_opts( th, cmdline_opts, duts=['dut'] )
  #th.set_param("top.dut.tile[1].construct", FuList=[MemUnitRTL,ShifterRTL])
  run_sim( th )

