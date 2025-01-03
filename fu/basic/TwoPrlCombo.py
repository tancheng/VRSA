"""
==========================================================================
TwoSeqComb.py
==========================================================================
Simple generic two parallelly combined functional units for CGRA tile.

Author : Cheng Tan
  Date : November 28, 2019
"""

from pymtl3 import *
from ...lib.basic.val_rdy.ifcs import ValRdyRecvIfcRTL as RecvIfcRTL
from ...lib.basic.val_rdy.ifcs import ValRdySendIfcRTL as SendIfcRTL
from ...lib.opt_type import *

class TwoPrlCombo(Component):

  def construct(s, DataType, PredicateType, CtrlType, Fu0, Fu1,
                num_inports, num_outports, data_mem_size):

    # Constants
    num_entries   = 2
    AddrType      = mk_bits( clog2( data_mem_size ) )
    CountType     = mk_bits( clog2( num_entries + 1 ) )

    # Interface
    s.recv_in        = [ RecvIfcRTL( DataType ) for _ in range( num_inports  ) ]
    s.recv_predicate = RecvIfcRTL( PredicateType )
    s.recv_opt       = RecvIfcRTL( CtrlType )
    s.send_out       = [ SendIfcRTL( DataType ) for _ in range( num_outports ) ]

    # Redundant interfaces for MemUnit
    s.to_mem_raddr   = SendIfcRTL( AddrType )
    s.from_mem_rdata = RecvIfcRTL( DataType )
    s.to_mem_waddr   = SendIfcRTL( AddrType )
    s.to_mem_wdata   = SendIfcRTL( DataType )

    # Components
    s.Fu0 = Fu0( DataType, PredicateType, CtrlType, 2, 1, data_mem_size )
    s.Fu1 = Fu1( DataType, PredicateType, CtrlType, 2, 1, data_mem_size )

    # Connections
    s.recv_in[0].msg      //= s.Fu0.recv_in[0].msg
    s.recv_in[1].msg      //= s.Fu0.recv_in[1].msg
    s.recv_in[2].msg      //= s.Fu1.recv_in[0].msg
    s.recv_in[3].msg      //= s.Fu1.recv_in[1].msg

    s.Fu0.send_out[0].msg //= s.send_out[0].msg
    s.Fu1.send_out[0].msg //= s.send_out[1].msg

    @update
    def update_signal():

      s.recv_in[0].rdy  @= s.Fu0.recv_in[0].rdy
      s.recv_in[1].rdy  @= s.Fu0.recv_in[1].rdy
      s.recv_in[2].rdy  @= s.Fu1.recv_in[0].rdy
      s.recv_in[3].rdy  @= s.Fu1.recv_in[1].rdy

      s.Fu0.recv_in[0].val @= s.recv_in[0].val
      s.Fu0.recv_in[1].val @= s.recv_in[1].val
      s.Fu1.recv_in[0].val @= s.recv_in[2].val
      s.Fu1.recv_in[1].val @= s.recv_in[3].val

      s.Fu0.recv_opt.val @= s.recv_opt.val
      s.Fu1.recv_opt.val @= s.recv_opt.val

      s.recv_opt.rdy @= s.Fu0.recv_opt.rdy & s.Fu1.recv_opt.rdy

      s.send_out[0].val @= s.Fu0.send_out[0].val
      s.send_out[1].val @= s.Fu1.send_out[0].val

      s.Fu0.send_out[0].rdy @= s.send_out[0].rdy
      s.Fu1.send_out[0].rdy @= s.send_out[1].rdy

      # Note that the predication for a combined FU should be identical/shareable,
      # which means the computation in different basic block cannot be combined.
      s.Fu0.recv_opt.msg.predicate @= s.recv_opt.msg.predicate
      s.Fu1.recv_opt.msg.predicate @= s.recv_opt.msg.predicate

      s.recv_predicate.rdy     @= s.Fu0.recv_predicate.rdy & \
                                  s.Fu1.recv_predicate.rdy

      s.Fu0.recv_predicate.val @= s.recv_predicate.val
      s.Fu1.recv_predicate.val @= s.recv_predicate.val

      s.Fu0.recv_predicate.msg @= s.recv_predicate.msg
      s.Fu1.recv_predicate.msg @= s.recv_predicate.msg

  def line_trace( s ):
    return s.Fu0.line_trace() + " ; " + s.Fu1.line_trace()

