local bit32 = require("bit32")

custom_rdp_proto = Proto("RDP-C", "Reliable Data Protocol")
local f_ack = ProtoField.bool("custom_rdp.ack", "ACK", 8, nil, 0x80)
local f_syn = ProtoField.bool("custom_rdp.syn", "SYN", 8, nil, 0x40)
local f_lst = ProtoField.bool("custom_rdp.lst", "LST", 8, nil, 0x20)
local f_fin = ProtoField.bool("custom_rdp.fin", "FIN", 8, nil, 0x10)
local f_sac = ProtoField.bool("custom_rdp.sack", "SACK", 8, nil, 0x08)
local f_seq_num = ProtoField.uint24("custom_rdp.seq_num", "Sequence Number")
local f_data = ProtoField.bytes("custom_rdp.data", "Data")
local f_data_ascii = ProtoField.string("custom_rdp.data_ascii", "Data (ASCII)")

custom_rdp_proto.fields = { f_ack, f_syn, f_lst, f_fin, f_sac, f_seq_num, f_data, f_data_ascii }

function custom_rdp_proto.dissector(buffer, pinfo, tree)

    if buffer:len() < 4 then
        return false
    end

    local flags = buffer(0, 1):uint()
    local seq_num = buffer(1, 3):uint()
    local has_flags = bit32.band(flags, 0xF8) ~= 0
    local has_data = buffer:len() > 4
    local has_no_extra_flags = bit32.band(flags, 0x70) ~= 0

    local is_rdp = has_flags or has_data or seq_num == 0 or has_no_extra_flags

    if not is_rdp then
        return false
    end

    pinfo.cols.protocol = custom_rdp_proto.name

    local subtree = tree:add(custom_rdp_proto, buffer(), "Reliable Data Protocol")

    subtree:add(f_ack, buffer(0, 1))
    subtree:add(f_syn, buffer(0, 1))
    subtree:add(f_lst, buffer(0, 1))
    subtree:add(f_fin, buffer(0, 1))
    subtree:add(f_sac, buffer(0, 1))
    subtree:add(f_seq_num, buffer(1, 3))

    if has_data then
        local data_field = buffer(4)
        subtree:add(f_data, data_field)
        
        local ascii_str = data_field:string()
        subtree:add(f_data_ascii, data_field, ascii_str)
    end

    return true
end

custom_rdp_proto:register_heuristic("udp", custom_rdp_proto.dissector)
