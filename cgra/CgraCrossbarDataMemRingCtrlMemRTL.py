"""
=========================================================================
CgraCrossbarDataMemRingCtrlMemRTL.py
=========================================================================

Author : Cheng Tan
  Date : Dec 22, 2024
"""

from pymtl3 import *
from ..controller.ControllerRTL import ControllerRTL
from ..fu.flexible.FlexibleFuRTL import FlexibleFuRTL
from ..fu.single.MemUnitRTL import MemUnitRTL
from ..fu.single.AdderRTL import AdderRTL
from ..lib.util.common import *
from ..lib.basic.en_rdy.ifcs import SendIfcRTL, RecvIfcRTL
from ..lib.basic.val_rdy.ifcs import ValRdySendIfcRTL
from ..lib.basic.val_rdy.ifcs import ValRdyRecvIfcRTL
from ..lib.opt_type import *
from ..mem.data.DataMemWithCrossbarRTL import DataMemWithCrossbarRTL
from ..noc.ChannelNormalRTL import ChannelNormalRTL
from ..noc.CrossbarSeparateRTL import CrossbarSeparateRTL
from ..noc.PyOCN.pymtl3_net.ocnlib.ifcs.positions import mk_ring_pos
from ..noc.PyOCN.pymtl3_net.ringnet.RingNetworkRTL import RingNetworkRTL
from ..tile.TileSeparateCrossbarRTL import TileSeparateCrossbarRTL

class CgraCrossbarDataMemRingCtrlMemRTL(Component):
  def construct(s, DataType, PredicateType, CtrlPktType, CtrlSignalType,
                NocPktType, CmdType, ControllerIdType, controller_id,
                width, height, ctrl_mem_size, data_mem_size_global,
                data_mem_size_per_bank, num_banks_per_cgra, num_ctrl,
                total_steps, FunctionUnit, FuList, controller2addr_map,
                preload_data = None, preload_const = None):

    s.num_tiles = width * height
    CtrlRingPos = mk_ring_pos(s.num_tiles)
    s.num_mesh_ports = 4
    CtrlAddrType = mk_bits(clog2(ctrl_mem_size))
    DataAddrType = mk_bits(clog2(data_mem_size_global))
    assert(data_mem_size_per_bank * num_banks_per_cgra <= \
           data_mem_size_global)

    # Interfaces
    # s.recv_waddr = [RecvIfcRTL(CtrlAddrType) for _ in range(s.num_tiles)]
    # s.recv_wopt = [RecvIfcRTL(CtrlSignalType) for _ in range(s.num_tiles)]
    s.recv_from_cpu_ctrl_pkt = ValRdyRecvIfcRTL(CtrlPktType)

    # Explicitly provides the ValRdyRecvIfcRTL in the library, as the
    # translation pass sometimes not able to distinguish the
    # EnRdyRecvIfcRTL from it.
    s.recv_from_noc = ValRdyRecvIfcRTL(NocPktType)
    s.send_to_noc = ValRdySendIfcRTL(NocPktType)

    # Interfaces on the boundary of the CGRA.
    s.recv_data_on_boundary_south = [RecvIfcRTL(DataType) for _ in range(width)]
    s.send_data_on_boundary_south = [SendIfcRTL(DataType) for _ in range(width)]
    s.recv_data_on_boundary_north = [RecvIfcRTL(DataType) for _ in range(width)]
    s.send_data_on_boundary_north = [SendIfcRTL(DataType) for _ in range(width)]

    s.recv_data_on_boundary_east = [RecvIfcRTL(DataType) for _ in range(height)]
    s.send_data_on_boundary_east = [SendIfcRTL(DataType) for _ in range(height)]
    s.recv_data_on_boundary_west = [RecvIfcRTL(DataType) for _ in range(height)]
    s.send_data_on_boundary_west = [SendIfcRTL(DataType) for _ in range(height)]

    # s.recv_towards_controller = RecvIfcRTL(DataType)
    # s.send_from_controller = SendIfcRTL(DataType)

    # Components
    if preload_const == None:
      preload_const = [[DataType(0, 0)] for _ in range(width*height)]
    s.tile = [TileSeparateCrossbarRTL(
        DataType, PredicateType, CtrlPktType, CtrlSignalType, ctrl_mem_size,
        data_mem_size_global, num_ctrl, total_steps, 4, 2,
        s.num_mesh_ports, s.num_mesh_ports,
        const_list = preload_const[i]) for i in range( s.num_tiles)]
    s.data_mem = DataMemWithCrossbarRTL(NocPktType, DataType,
                                        data_mem_size_global,
                                        data_mem_size_per_bank,
                                        num_banks_per_cgra,
                                        height, height,
                                        preload_data)
    s.controller = ControllerRTL(ControllerIdType, CmdType, CtrlPktType,
                                 NocPktType, DataType, DataAddrType,
                                 controller_id, controller2addr_map)
    s.ctrl_ring = RingNetworkRTL(CtrlPktType, CtrlRingPos, s.num_tiles, 0)

    # Connections
    # Connects data memory with controller.
    # s.data_mem.recv_from_noc //= s.controller.send_to_master
    # s.data_mem.send_to_noc //= s.controller.recv_from_master

    # The last `recv_raddr` is reserved to connect the controller.
    s.data_mem.recv_raddr[height] //= s.controller.send_to_master_load_request_addr
    s.data_mem.recv_waddr[height] //= s.controller.send_to_master_store_request_addr
    s.data_mem.recv_wdata[height] //= s.controller.send_to_master_store_request_data
    # Reserved ...
    s.data_mem.recv_from_noc_rdata //= s.controller.send_to_master_load_response_data
    # Reserved ...
    s.data_mem.send_to_noc_load_request_pkt //= s.controller.recv_from_master_load_request_pkt
    s.data_mem.send_to_noc_load_response_pkt //= s.controller.recv_from_master_load_response_pkt
    s.data_mem.send_to_noc_store_pkt //= s.controller.recv_from_master_store_request_pkt

    s.recv_from_noc //= s.controller.recv_from_noc
    s.send_to_noc //= s.controller.send_to_noc

    # Connects the ctrl interface between CPU and controller.
    s.recv_from_cpu_ctrl_pkt //= s.controller.recv_from_cpu_ctrl_pkt

    # s.recv_towards_controller //= s.controller.recv_from_master
    # s.send_from_controller //= s.controller.send_to_master

    # Connects ring with each control memory.
    for i in range(s.num_tiles):
      s.ctrl_ring.send[i] //= s.tile[i].recv_ctrl_pkt

    s.ctrl_ring.recv[0] //= s.controller.send_to_ctrl_ring_ctrl_pkt
    for i in range(1, s.num_tiles):
      s.ctrl_ring.recv[i].val //= 0
      s.ctrl_ring.recv[i].msg //= CtrlPktType()

    for i in range(s.num_tiles):
      # s.recv_waddr[i] //= s.tile[i].recv_waddr
      # s.recv_wopt[i] //= s.tile[i].recv_wopt

      if i // width > 0:
        s.tile[i].send_data[PORT_SOUTH] //= s.tile[i-width].recv_data[PORT_NORTH]

      if i // width < height - 1:
        s.tile[i].send_data[PORT_NORTH] //= s.tile[i+width].recv_data[PORT_SOUTH]

      if i % width > 0:
        s.tile[i].send_data[PORT_WEST] //= s.tile[i-1].recv_data[PORT_EAST]

      if i % width < width - 1:
        s.tile[i].send_data[PORT_EAST] //= s.tile[i+1].recv_data[PORT_WEST]

      if i // width == 0:
        s.tile[i].send_data[PORT_SOUTH] //= s.send_data_on_boundary_south[i % width]
        s.tile[i].recv_data[PORT_SOUTH] //= s.recv_data_on_boundary_south[i % width]

      if i // width == height - 1:
        s.tile[i].send_data[PORT_NORTH] //= s.send_data_on_boundary_north[i % width]
        s.tile[i].recv_data[PORT_NORTH] //= s.recv_data_on_boundary_north[i % width]

      if i % width == 0:
        s.tile[i].send_data[PORT_WEST] //= s.send_data_on_boundary_west[i // width]
        s.tile[i].recv_data[PORT_WEST] //= s.recv_data_on_boundary_west[i // width]

      if i % width == width - 1:
        s.tile[i].send_data[PORT_EAST] //= s.send_data_on_boundary_east[i // width]
        s.tile[i].recv_data[PORT_EAST] //= s.recv_data_on_boundary_east[i // width]

      # if i // width == 0:
      #   s.tile[i].send_data[PORT_SOUTH].rdy //= 0
      #   s.tile[i].recv_data[PORT_SOUTH].en //= 0
      #   s.tile[i].recv_data[PORT_SOUTH].msg //= DataType(0, 0)

      # if i // width == height - 1:
      #   s.tile[i].send_data[PORT_NORTH].rdy //= 0
      #   s.tile[i].recv_data[PORT_NORTH].en //= 0
      #   s.tile[i].recv_data[PORT_NORTH].msg //= DataType(0, 0)

      # if i % width == 0:
      #   s.tile[i].send_data[PORT_WEST].rdy //= 0
      #   s.tile[i].recv_data[PORT_WEST].en //= 0
      #   s.tile[i].recv_data[PORT_WEST].msg //= DataType(0, 0)

      # if i % width == width - 1:
      #   s.tile[i].send_data[PORT_EAST].rdy //= 0
      #   s.tile[i].recv_data[PORT_EAST].en //= 0
      #   s.tile[i].recv_data[PORT_EAST].msg //= DataType(0, 0)

      if i % width == 0:
        s.tile[i].to_mem_raddr //= s.data_mem.recv_raddr[i//width]
        s.tile[i].from_mem_rdata //= s.data_mem.send_rdata[i//width]
        s.tile[i].to_mem_waddr //= s.data_mem.recv_waddr[i//width]
        s.tile[i].to_mem_wdata //= s.data_mem.recv_wdata[i//width]
      else:
        s.tile[i].to_mem_raddr.rdy //= 0
        s.tile[i].from_mem_rdata.en //= 0
        s.tile[i].from_mem_rdata.msg //= DataType(0, 0)
        s.tile[i].to_mem_waddr.rdy //= 0
        s.tile[i].to_mem_wdata.rdy //= 0

  # Line trace
  def line_trace( s ):
    # str = "||".join([ x.element.line_trace() for x in s.tile ])
    # str += " :: [" + s.data_mem.line_trace() + "]"
    res = "||\n".join([ (("[tile"+str(i)+"]: ") + x.line_trace() + x.ctrl_mem.line_trace())
                              for (i,x) in enumerate(s.tile) ])
    res += "\n :: [" + s.data_mem.line_trace() + "]    \n"
    return res

