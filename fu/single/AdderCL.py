"""
==========================================================================
AdderCL.py
==========================================================================
Adder for CGRA tile. The latency is parameterizable.

Author : Cheng Tan
  Date : Aug 5, 2023
"""


from pymtl3 import *
from ..basic.Fu import Fu
from ...lib.basic.en_rdy.ifcs import SendIfcRTL, RecvIfcRTL
from ...lib.opt_type import *


class AdderCL( Fu ):

  def construct( s, DataType, PredicateType, CtrlType,
                 num_inports, num_outports, data_mem_size, latency = 1 ):

    super( AdderCL, s ).construct( DataType, PredicateType, CtrlType,
                                   num_inports, num_outports,
                                   data_mem_size, latency )

    # Constant
    s.const_one = DataType(1, 1)
    FuInType    = mk_bits( clog2( num_inports + 1 ) )
    num_entries = 2
    CountType   = mk_bits( clog2( num_entries + 1 ) )
    idx_nbits   = clog2( num_inports )
    LatencyType = mk_bits( clog2( latency + 1 ) )

    # Component
    s.in0     = Wire( FuInType )
    s.in1     = Wire( FuInType )
    s.in0_idx = Wire( idx_nbits )
    s.in1_idx = Wire( idx_nbits )

    s.in0_idx //= s.in0[0:idx_nbits]
    s.in1_idx //= s.in1[0:idx_nbits]

    @update
    def comb_logic():

      s.in0 @= 0
      s.in1 @= 0
      s.recv_predicate.rdy @= 0
      # For pick input register
      for i in range( num_inports ):
        s.recv_in[i].rdy @= b1( 0 )

      for i in range( num_outports ):
        s.send_out[i].en  @= s.recv_opt.en
        s.send_out[i].msg @= DataType()

      s.recv_predicate.rdy @= b1( 0 )

      if s.recv_opt.en:
        if s.recv_opt.msg.fu_in[0] != 0:
          s.in0 @= zext(s.recv_opt.msg.fu_in[0] - 1, FuInType)
          s.recv_in[s.in0_idx].rdy @= b1( 1 )
        if s.recv_opt.msg.fu_in[1] != 0:
          s.in1 @= zext(s.recv_opt.msg.fu_in[1] - 1, FuInType)
          s.recv_in[s.in1_idx].rdy @= b1( 1 )
        if s.recv_opt.msg.predicate == b1( 1 ):
          s.recv_predicate.rdy @= b1( 1 )

      s.send_out[0].msg.predicate @= s.recv_in[s.in0_idx].msg.predicate & \
                                     s.recv_in[s.in1_idx].msg.predicate


#      s.send_out[0].en = s.recv_opt.en

      if s.recv_opt.msg.ctrl == OPT_ADD:
        s.send_out[0].msg.payload @= s.recv_in[s.in0_idx].msg.payload + s.recv_in[s.in1_idx].msg.payload
        s.send_out[0].msg.predicate @= s.recv_in[s.in0_idx].msg.predicate & s.recv_in[s.in1_idx].msg.predicate
        if s.recv_opt.en & ( (s.recv_in_count[s.in0_idx] == 0) | \
                             (s.recv_in_count[s.in1_idx] == 0) ):
          s.recv_in[s.in0_idx].rdy @= b1( 0 )
          s.recv_in[s.in1_idx].rdy @= b1( 0 )
          s.send_out[0].msg.predicate @= b1( 0 )
      elif s.recv_opt.msg.ctrl == OPT_ADD_CONST:
        s.send_out[0].msg.payload @= s.recv_in[s.in0_idx].msg.payload + s.recv_const.msg.payload
        s.send_out[0].msg.predicate @= s.recv_in[s.in0_idx].msg.predicate
      elif s.recv_opt.msg.ctrl == OPT_INC:
        s.send_out[0].msg.payload @= s.recv_in[s.in0_idx].msg.payload + s.const_one.payload
        s.send_out[0].msg.predicate @= s.recv_in[s.in0_idx].msg.predicate
      elif s.recv_opt.msg.ctrl == OPT_SUB:
        s.send_out[0].msg.payload @= s.recv_in[s.in0_idx].msg.payload - s.recv_in[s.in1_idx].msg.payload
        s.send_out[0].msg.predicate @= s.recv_in[s.in0_idx].msg.predicate
        if s.recv_opt.en & ( (s.recv_in_count[s.in0_idx] == 0) | \
                             (s.recv_in_count[s.in1_idx] == 0) ):
          s.recv_in[s.in0_idx].rdy @= b1( 0 )
          s.recv_in[s.in1_idx].rdy @= b1( 0 )
          s.send_out[0].msg.predicate @= b1( 0 )
      elif s.recv_opt.msg.ctrl == OPT_PAS:
        s.send_out[0].msg.payload @= s.recv_in[s.in0_idx].msg.payload
        s.send_out[0].msg.predicate @= s.recv_in[s.in0_idx].msg.predicate
      else:
        for j in range( num_outports ):
          s.send_out[j].en @= b1( 0 )

      if s.recv_opt.msg.predicate == b1( 1 ):
        s.send_out[0].msg.predicate @= s.send_out[0].msg.predicate & \
                                       s.recv_predicate.msg.predicate
