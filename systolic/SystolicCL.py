"""
=========================================================================
SystolicCL.py
=========================================================================

Author : Cheng Tan
  Date : May 24, 2020
"""


from pymtl3 import *
from ..lib.basic.en_rdy.ifcs import SendIfcRTL, RecvIfcRTL
from ..lib.opt_type import *
from ..mem.data.DataMemCL import DataMemCL
from ..noc.CrossbarRTL import CrossbarRTL
from ..noc.ChannelRTL import ChannelRTL
from ..tile.TileCL import TileCL


class SystolicCL( Component ):

  def construct( s, FunctionUnit, FuList, DataType, PredicateType,
                 CtrlType, width, height, ctrl_mem_size, data_mem_size,
                 num_ctrl, total_steps, preload_ctrl, preload_data,
                 preload_const ):

    # Constant
    NORTH = 0
    SOUTH = 1
    WEST  = 2
    EAST  = 3
    s.num_tiles = width * height
    s.num_mesh_ports = 4
    AddrType = mk_bits( clog2( ctrl_mem_size ) )

    s.send_data = [ SendIfcRTL( DataType ) for _ in range ( height-1 ) ]

    # Components
    s.tile = [ TileCL( FunctionUnit, FuList, DataType, PredicateType,
                       CtrlType, ctrl_mem_size, data_mem_size, num_ctrl,
                       total_steps, preload_const[i], preload_ctrl[i] )
                       for i in range( s.num_tiles ) ]
    s.data_mem = DataMemCL( DataType, data_mem_size, height, height,
                            preload_data )

    # Connections

    for i in range( s.num_tiles):

      if i // width > 0:
        s.tile[i].send_data[SOUTH] //= s.tile[i-width].recv_data[NORTH]

      if i // width < height - 1:
        s.tile[i].send_data[NORTH] //= s.tile[i+width].recv_data[SOUTH]

      if i % width > 0:
        s.tile[i].send_data[WEST] //= s.tile[i-1].recv_data[EAST]

      if i % width < width - 1:
        s.tile[i].send_data[EAST] //= s.tile[i+1].recv_data[WEST]

      if i // width == 0:
        s.tile[i].send_data[SOUTH].rdy //= 0
        s.tile[i].recv_data[SOUTH].en  //= 0
        s.tile[i].recv_data[SOUTH].msg //= DataType( 0, 0 )

      if i // width == height - 1:
        s.tile[i].send_data[NORTH].rdy  //= 0
        s.tile[i].recv_data[NORTH].en   //= 0
        s.tile[i].recv_data[NORTH].msg  //= DataType( 0, 0 )

      if i % width == 0:
        s.tile[i].send_data[WEST].rdy  //= 0
        s.tile[i].recv_data[WEST].en   //= 0
        s.tile[i].recv_data[WEST].msg  //= DataType( 0, 0 )

      if i % width == width - 1:
        if i // width != 0:
          s.tile[i].send_data[EAST] //= s.send_data[i//width-1]
          s.tile[i].recv_data[EAST].en   //= 0
          s.tile[i].recv_data[EAST].msg  //= DataType( 0, 0 )
        else:
          s.tile[i].send_data[EAST].rdy  //= 0
          s.tile[i].recv_data[EAST].en   //= 0
          s.tile[i].recv_data[EAST].msg  //= DataType( 0, 0 )

      if i // width == 0:
        s.tile[i].to_mem_raddr   //= s.data_mem.recv_raddr[i % width]
        s.tile[i].from_mem_rdata //= s.data_mem.send_rdata[i % width]
        s.tile[i].to_mem_waddr   //= s.data_mem.recv_waddr[i % width]
        s.tile[i].to_mem_wdata   //= s.data_mem.recv_wdata[i % width]
      else:
        s.tile[i].to_mem_raddr.rdy //= 0
        s.tile[i].from_mem_rdata.en //= 0
        s.tile[i].from_mem_rdata.msg //= DataType(0, 0)
        s.tile[i].to_mem_waddr.rdy //= 0
        s.tile[i].to_mem_wdata.rdy //= 0

  # Line trace
  def line_trace( s ):
    str = "||\n".join([ (x.line_trace() + x.ctrl_mem.line_trace())
                      for x in s.tile ])
    str += "\n[data] :: [" + s.data_mem.line_trace() + "]\n"
    return str

