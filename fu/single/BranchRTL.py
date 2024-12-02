"""
==========================================================================
BranchRTL.py
==========================================================================
Functional unit Branch for CGRA tile.

Author : Cheng Tan
  Date : December 1, 2019
"""


from pymtl3 import *
from ..basic.Fu import Fu
from ...lib.basic.en_rdy.ifcs import SendIfcRTL, RecvIfcRTL
from ...lib.opt_type import *


class BranchRTL( Fu ):

  def construct( s, DataType, PredicateType, CtrlType,
                 num_inports, num_outports, data_mem_size ):

    super( BranchRTL, s ).construct( DataType, PredicateType, CtrlType,
                                     num_inports, num_outports, data_mem_size )

    FuInType    = mk_bits( clog2( num_inports + 1 ) )
    num_entries = 2
    CountType   = mk_bits( clog2( num_entries + 1 ) )
    s.first     = Wire( b1 )

    ZeroType    = mk_bits( s.const_zero.payload.nbits )

    # TODO: declare in0 as wire
    s.in0 = Wire( FuInType )

    idx_nbits = clog2( num_inports )
    s.in0_idx = Wire( idx_nbits )

    s.in0_idx //= s.in0[0:idx_nbits]

    @update
    def comb_logic():

      # For pick input register
      s.in0 @= 0
      # in1 = FuInType( 0 )
      for i in range( num_inports ):
        s.recv_in[i].rdy @= b1( 0 )
      for i in range( num_outports ):
        s.send_out[i].en  @= s.recv_opt.en
        s.send_out[i].msg @= DataType()

      s.recv_predicate.rdy @= b1( 0 )

      if s.recv_opt.en:
        if s.recv_opt.msg.fu_in[0] != FuInType( 0 ):
          s.in0 @= s.recv_opt.msg.fu_in[0] - FuInType( 1 )
          s.recv_in[s.in0_idx].rdy @= b1( 1 )
#        if s.recv_opt.msg.fu_in[1] != FuInType( 0 ):
#          in1 = s.recv_opt.msg.fu_in[1] - FuInType( 1 )
#          s.recv_in[in1].rdy = b1( 1 )

        if s.recv_opt.msg.predicate == b1( 1 ):
          s.recv_predicate.rdy @= b1( 1 )

      if s.recv_opt.msg.ctrl == OPT_BRH:
        # Branch is only used to set predication rather than delivering value.
        s.send_out[0].msg @= DataType(ZeroType( 0 ), b1( 0 ), b1( 0 ), b1( 0 ) )
        s.send_out[1].msg @= DataType(ZeroType( 0 ), b1( 0 ), b1( 0 ), b1( 0 ) )
        if s.recv_in[s.in0_idx].msg.payload == s.const_zero.payload:
          s.send_out[0].msg.predicate @= Bits1( 1 )
          s.send_out[1].msg.predicate @= Bits1( 0 )
        else:
          s.send_out[0].msg.predicate @= Bits1( 0 )
          s.send_out[1].msg.predicate @= Bits1( 1 )
      elif s.recv_opt.msg.ctrl == OPT_BRH_START:
        s.send_out[0].msg @= DataType(ZeroType( 0 ), b1( 0 ), b1( 0 ), b1( 0 ) )
        s.send_out[1].msg @= DataType(ZeroType( 0 ), b1( 0 ), b1( 0 ), b1( 0 ) )
        if s.first:
          s.send_out[0].msg.predicate @= Bits1( 1 )
          s.send_out[1].msg.predicate @= Bits1( 0 )
        else:
          s.send_out[0].msg.predicate @= Bits1( 0 )
          s.send_out[1].msg.predicate @= Bits1( 1 )

      else:
        for j in range( num_outports ):
          s.send_out[j].en @= b1( 0 )

      if (s.recv_opt.msg.predicate == 1) & (s.recv_opt.msg.ctrl != OPT_BRH_START):
        # The operation executed on the first cycle gets no input predicate.
        s.send_out[0].msg.predicate @= s.send_out[0].msg.predicate & \
                                       s.recv_predicate.msg.predicate
        s.send_out[1].msg.predicate @= s.send_out[1].msg.predicate & \
                                       s.recv_predicate.msg.predicate

    # branch_start could be the entry of a function, which is executed by
    # only once.
    @update_ff
    def br_start_once():
      if s.reset:
        s.first <<= b1( 1 )
      if s.recv_opt.msg.ctrl == OPT_BRH_START:
        s.first <<= b1( 0 )



  def line_trace( s ):
    symbol0 = "?"
    symbol1 = "?"
    winner  = "nobody"
    if s.recv_opt.msg.ctrl == OPT_BRH_START:
      symbol0 = " "
      symbol1 = " "
      winner = "nobody"
    elif s.send_out[0].msg.predicate == Bits1(1):
      symbol0 = "*"
      symbol1 = " "
      winner  = "false "
    elif s.send_out[1].msg.predicate == Bits1(1):
      symbol0 = " "
      symbol1 = "*"
      winner  = " true "
    return f'[{s.recv_in[0].msg}|{s.recv_in[1].msg}] => ([{s.send_out[0].msg} {symbol0}] ({winner}) [{s.send_out[1].msg}(first:{s.first}) {symbol1}])'
