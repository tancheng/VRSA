"""
==========================================================================
MemUnitRTL.py
==========================================================================
Scratchpad memory access unit for (the left most) CGRA tiles.

Author : Cheng Tan
  Date : November 29, 2019
"""


from pymtl3 import *
from ..basic.Fu import Fu
from ...lib.basic.en_rdy.ifcs import SendIfcRTL, RecvIfcRTL
from ...lib.opt_type import *


class MemUnitRTL( Component ):

  def construct( s, DataType, PredicateType, CtrlType,
                 num_inports, num_outports, data_mem_size ):

    # Constant
    AddrType      = mk_bits( clog2( data_mem_size ) )
    num_entries   = 2
    CountType     = mk_bits( clog2( num_entries + 1 ) )
    FuInType      = mk_bits( clog2( num_inports + 1 ) )

    # Interface
    s.recv_in        = [ RecvIfcRTL( DataType ) for _ in range( num_inports ) ]
    s.recv_in_count  = [ InPort( CountType ) for _ in range( num_inports ) ]
    s.recv_predicate = RecvIfcRTL( PredicateType )
    s.recv_const     = RecvIfcRTL( DataType )
    s.recv_opt       = RecvIfcRTL( CtrlType )
    s.send_out       = [ SendIfcRTL( DataType ) for _ in range( num_outports ) ]

    # Interface to the data sram, need to interface them with
    # the data memory module in top level
    s.to_mem_raddr   = SendIfcRTL( AddrType )
    s.from_mem_rdata = RecvIfcRTL( DataType )
    s.to_mem_waddr   = SendIfcRTL( AddrType )
    s.to_mem_wdata   = SendIfcRTL( DataType )
    # s.initial_carry_in  = InPort( b1 )
    # s.initial_carry_out = OutPort( b1 )

    s.in0 = Wire( FuInType )
    s.in1 = Wire( FuInType )

    idx_nbits = clog2( num_inports )
    s.in0_idx = Wire( idx_nbits )
    s.in1_idx = Wire( idx_nbits )

    s.in0_idx //= s.in0[0:idx_nbits]
    s.in1_idx //= s.in1[0:idx_nbits]

    # Components
    s.recv_rdy_vector = Wire( num_outports )
    s.recv_in_en_vector = Wire( num_inports )

    @update
    def comb_logic():

      # For pick input register
      s.in0 @= FuInType( 0 )
      s.in1 @= FuInType( 0 )
      for i in range( num_inports ):
        s.recv_in[i].rdy @= b1( 0 )

      s.recv_predicate.rdy @= b1( 0 )

      if s.recv_opt.en:
        if s.recv_opt.msg.fu_in[0] != 0:
          s.in0 @= zext( s.recv_opt.msg.fu_in[0] - 1, FuInType )
          s.recv_in[s.in0_idx].rdy @= b1( 1 )
        if s.recv_opt.msg.fu_in[1] != 0:
          s.in1 @= zext( s.recv_opt.msg.fu_in[1] - 1, FuInType )
          s.recv_in[s.in1_idx].rdy @= b1( 1 )
        if s.recv_opt.msg.predicate == b1( 1 ):
          s.recv_predicate.rdy @= b1( 1 )

      for j in range( num_outports ):
        # s.recv_const.rdy @= s.send_out[j].rdy | s.recv_const.rdy
        s.recv_rdy_vector[j] @= s.send_out[j].rdy

      # for j in range( num_outports ):
      #   s.recv_opt.rdy @= s.send_out[j].rdy | s.recv_opt.rdy
      s.recv_const.rdy @= reduce_or( s.recv_rdy_vector )
      s.recv_opt.rdy   @= reduce_or( s.recv_rdy_vector )

      # for j in range( num_outports ):
      #   for i in range( num_inports ):
      #     s.send_out[j].en @= s.recv_in[i].en | s.send_out[j].en
      #   s.send_out[j].en @= s.send_out[j].en & s.recv_opt.en

      for i in range( num_inports ):
        s.recv_in_en_vector[i] @= s.recv_in[i].en

      for j in range( num_outports ):
        s.send_out[j].en @= s.recv_opt.en & reduce_or( s.recv_in_en_vector)

      s.send_out[0].msg     @= s.from_mem_rdata.msg

      s.to_mem_waddr.en     @= 0
      s.to_mem_waddr.msg    @= AddrType()
      s.to_mem_wdata.en     @= 0
      s.to_mem_wdata.msg    @= DataType()
      s.to_mem_raddr.en     @= 0
      s.to_mem_raddr.msg    @= AddrType()
      s.from_mem_rdata.rdy  @= 0

      if s.recv_opt.msg.ctrl == OPT_LD:
        s.recv_in[s.in0_idx].rdy     @= s.to_mem_raddr.rdy
        s.recv_in[s.in1_idx].rdy     @= s.from_mem_rdata.rdy
        # s.to_mem_raddr.msg   @= AddrType( s.recv_in[s.in0_idx].msg.payload )
        s.to_mem_raddr.msg   @= AddrType( s.recv_in[s.in0_idx].msg.payload[0:AddrType.nbits] )
        s.to_mem_raddr.en    @= s.recv_in[s.in0_idx].en
        s.from_mem_rdata.rdy @= s.send_out[0].rdy
        s.send_out[0].msg    @= s.from_mem_rdata.msg
        s.send_out[0].en     @= s.recv_opt.en
        s.send_out[0].msg.predicate @= s.recv_in[s.in0_idx].msg.predicate

      # LD_CONST indicates the address is a const.
      elif s.recv_opt.msg.ctrl == OPT_LD_CONST:
        for i in range( num_inports):
          s.recv_in[i].rdy @= b1( 0 )
        s.recv_const.rdy     @= s.to_mem_raddr.rdy
        s.to_mem_raddr.msg   @= AddrType( s.recv_const.msg.payload[0:AddrType.nbits] )
        s.to_mem_raddr.en    @= s.recv_const.en
        s.from_mem_rdata.rdy @= s.send_out[0].rdy
        s.send_out[0].msg    @= s.from_mem_rdata.msg
        s.send_out[0].en     @= s.recv_opt.en
        # Const's predicate will always be true.
        s.send_out[0].msg.predicate @= b1( 1 )

      elif s.recv_opt.msg.ctrl == OPT_STR:
        # s.send_out[0].en     @= s.from_mem_rdata.en & s.recv_in[s.in0_idx].en & s.recv_in[s.in1_idx].en
        s.recv_in[s.in0_idx].rdy   @= s.to_mem_waddr.rdy
        s.recv_in[s.in1_idx].rdy   @= s.to_mem_wdata.rdy
        # s.to_mem_waddr.msg @= AddrType( s.recv_in[0].msg.payload )
        s.to_mem_waddr.msg @= AddrType( s.recv_in[0].msg.payload[0:AddrType.nbits] )
        s.to_mem_waddr.en  @= s.recv_in[s.in0_idx].en
        s.to_mem_wdata.msg @= s.recv_in[s.in1_idx].msg
        s.to_mem_wdata.en  @= s.recv_in[s.in1_idx].en

        # `send_out` is meaningless for store operation.
        s.send_out[0].en   @= b1( 0 )
        s.send_out[0].msg  @= s.to_mem_wdata.msg
        # s.send_out[0].msg.predicate @= s.recv_in[s.in0_idx].msg.predicate & \
        #                                s.recv_in[s.in1_idx].msg.predicate
        s.send_out[0].msg.predicate @= b1(0)
        if s.recv_opt.en & ( (s.recv_in_count[s.in0_idx] == 0) | \
                             (s.recv_in_count[s.in1_idx] == 0) ):
          s.recv_in[s.in0_idx].rdy @= b1( 0 )
          s.recv_in[s.in1_idx].rdy @= b1( 0 )
          # s.send_out[0].msg.predicate @= b1( 0 )

      # STR_CONST indicates the address is a const.
      elif s.recv_opt.msg.ctrl == OPT_STR_CONST:
        s.recv_const.rdy @= s.to_mem_waddr.rdy

        # Only needs one input register to indicate the storing data.
        s.recv_in[s.in0_idx].rdy @= s.to_mem_wdata.rdy
        s.to_mem_waddr.msg @= AddrType( s.recv_const.msg.payload[0:AddrType.nbits] )
        s.to_mem_waddr.en  @= s.recv_const.en
        s.to_mem_wdata.msg @= s.recv_in[s.in0_idx].msg
        s.to_mem_wdata.en  @= s.recv_in[s.in0_idx].en

        # `send_out` is meaningless for store operation.
        s.send_out[0].en   @= b1( 0 )
        s.send_out[0].msg  @= s.to_mem_wdata.msg
        s.send_out[0].msg.predicate @= b1(0)
        if s.recv_opt.en & (s.recv_in_count[s.in0_idx] == 0):
          s.recv_in[s.in0_idx].rdy @= b1( 0 )

      else:
        for j in range( num_outports ):
          s.send_out[j].en @= b1( 0 )

      if s.recv_opt.msg.predicate == b1( 1 ):
        s.send_out[0].msg.predicate @= s.send_out[0].msg.predicate & \
                                       s.recv_predicate.msg.predicate

  def line_trace( s ):
    opt_str = " #"
    if s.recv_opt.en:
      opt_str = OPT_SYMBOL_DICT[s.recv_opt.msg.ctrl]
    out_str = ",".join([str(x.msg) for x in s.send_out])
    recv_str = ",".join([str(x.msg) for x in s.recv_in])
    return f'[recv: {recv_str}] {opt_str}(P{s.recv_opt.msg.predicate}) (const: {s.recv_const.msg}) ] = [out: {out_str}] (s.recv_opt.rdy: {s.recv_opt.rdy}, {OPT_SYMBOL_DICT[s.recv_opt.msg.ctrl]}, send[0].en: {s.send_out[0].en}) <{s.recv_const.en}|{s.recv_const.msg}>'
