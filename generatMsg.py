def buildHeader(name, msgID, sendSize):
    header_template = f"kern_return_t {name}(mach_port_t port){{\n\
    mach_msg_header_t *msg = malloc(0x4000);\n\
    memset(msg, 0, 0x4000);\n\
    kern_return_t kr = prepareVerySimpleMessage(msg, port, {msgID}, {sendSize});\n\
    if(kr != KERN_SUCCESS){{\n\
        free(msg);\n\
        return kr;\n\
    }}\n"
    return header_template


def buildFooter():
    footer_template = "    kr = mach_msg(msg, MACH_SEND_MSG|MACH_RCV_MSG, msg->msgh_size, 0x4000,  msg->msgh_local_port, MACH_MSG_TIMEOUT_NONE, MACH_PORT_NULL);\n\
        if(kr == KERN_SUCCESS){\n\
            \n\
        }\n\
        free(msg);\n\
        return kr;\n\
}\n"
    return footer_template


def build_fields(fields_info):
    fields_info_template = ""

    for key, value in fields_info.items():
        value_len = value["length"]
        value_type = value["type"]
        if value_type == "num":
            size_type = "uint32_t"
            if value_len == 1:
                size_type = "char"
            elif value_len == 2:
                size_type = "uint16_t"
            elif value_len == 4:
                size_type = "uint32_t"
            elif value_len == 8:
                size_type = "uint64_t"

            value_subtype = value["subtype"]
            if value_subtype == "range":
                min = value["min"]
                max = value["max"]
                fields_info_template += f"    *({size_type}*)((char*)msg+{
                    key}) = random_number_between({min},{max});\n"
            if value_subtype == "enum":
                enums = value["enums"]
                enums = "[" + ", ".join(f"@{x}" for x in enums) + "]"
                fields_info_template += f"    *({size_type}*)((char*)msg+{
                    key}) = random_from_array((NSMutableArray*)@{enums});\n"

        elif value_type == "float":
            fields_info_template += f"    *(float*)((char*)msg+{
                key}) = randomFloat();\n"
        elif value_type == "id":
            value_subtype = value["subtype"]
            fields_info_template += f"    *({size_type}*)((char*)msg+{key}) = random{
                value_subtype}ID();\n"

    return fields_info_template


def build_complicated_msg(descriptorCount, descriptors):
    code_template = ""
    code_template += "    msg->msgh_bits |= MACH_MSGH_BITS_COMPLEX;\n"
    code_template += f"    *(uint32_t*)((char*)msg+0x18) = {
        descriptorCount};\n"
    cur_loc = 0x1c
    for descriptor in descriptors:
        if descriptor == 'ool':
            code_template += f"    prepareOOL_Descriptor((char*)msg+{
                cur_loc}, buf, bufSize, MACH_MSG_VIRTUAL_COPY);\n"
            cur_loc += 0x10
        elif descriptor == 'port':
            code_template += "    mach_port_t port1 = MACH_PORT_NULL;\n"
            code_template += "    kr = mach_port_allocate(mach_task_self(), MACH_PORT_RIGHT_RECEIVE, &port1);\n"
            code_template += "    if(kr != KERN_SUCCESS){\n"
            code_template += "        free(msg);\n"
            code_template += "        return kr;\n"
            code_template += "    }\n"
            code_template += f"    preparePort_Descriptor((char*)msg+{
                cur_loc}, port1, MACH_MSG_TYPE_MAKE_SEND);\n"
            cur_loc += 0xc
    return code_template


def build_code():
    msgName = "test"
    msgID = 29200
    sendSize = 0x28
    fields_info = {"0x1c": {"length": 4, "type": "num", "subtype": "range", "min": 2, "max": 10},
                   "0x20": {"length": 4, "type": "float", "subtype": ""},
                   "0x24": {"length": 4, "type": "id", "subtype": "Window"},
                   "0x28": {"length": 4, "type": "num", "subtype": "enum", "enums": [1, 2, 3, 4, 5, 6, 7, 8]},
                   }
    descriptorCount = 2
    descriptors = ['ool', 'port']

    header = buildHeader(msgName, msgID, sendSize)
    fields_info_str = build_fields(fields_info)
    complicated_msg = build_complicated_msg(descriptorCount, descriptors)
    footer = buildFooter()
    return header + fields_info_str + complicated_msg + footer


print(build_code())


'''
//if complicated message\
    msg->msgh_bits |= MACH_MSGH_BITS_COMPLEX;\
    *(uint32_t*)((char*)msg+0x18) = ${descriptorCount};\
//if ool\
    prepareOOL_Descriptor((char*)msg+${index}, buf, bufSize, MACH_MSG_VIRTUAL_COPY);\
//if port\
    mach_port_t port1 = MACH_PORT_NULL;\
    kr = mach_port_allocate(mach_task_self(), MACH_PORT_RIGHT_RECEIVE, &port1);\
    if(kr != KERN_SUCCESS){\
        free(msg);\
        return kr;\
    }\
    preparePort_Descriptor((char*)msg+${index}, port1, MACH_MSG_TYPE_MAKE_SEND);\
//...\
//剩下的就是处理每个偏移了\
    //1字节\
    *(char*)((char*)msg+${key}) = xxx\
    //2字节\
    *(uint16_t*)((char*)msg+${key}) = xxx\
    //4字节\
    *(uint32_t*)((char*)msg+${key}) = xxx\
    //8字节\
    *(uint64_t*)((char*)msg+${key}) = xxx\
//这里的xxx要取决于设置的类型，目前有以下几种\
//如果是数字\
    //如果是纯随机 xxx = random_number();\
    //如果是一个范围 xxx = random_number_between(${min},${max});\
    //如果是某个值里取一个值, xxx = random_from_array((NSMutableArray*)@[@v1, @v2,@v3]);\
    //如果是float， xxx = randomFloat();\
//如果是xxxID\
    // xxx = randomxxxID();\
//后面的不用改\
    kr = mach_msg(&msg->header, MACH_SEND_MSG|MACH_RCV_MSG, msg->header.msgh_size, 0x4000,  msg->header.msgh_local_port, MACH_MSG_TIMEOUT_NONE, MACH_PORT_NULL);\
    if(kr == KERN_SUCCESS){\
        \
    }\
    free(msg);\
    return kr\
}"
'''
