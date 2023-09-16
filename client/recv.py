import random
import struct
import typing

import buffer

l = []
c = []


def data_creator(bags: int) -> typing.Generator:
    global l, c

    data: bytes = (
        b"\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09\x10\x11\x12\x13\x14\x15\x16\x17\x18\x19\x20\x21\x22\x23\x24\x25\x26"
        b"\x27\x28\x29\x30\x31\x32\x33\x34\x35\x36\x37\x38\x39\x40\x41\x42\x43\x44\x45\x46\x47\x48\x49\x50\x51\x52"
        b"\x53\x54\x55\x56\x57\x58\x59\x60\x61\x62\x63"
    )

    recv_data, real_len, real_context = data_divider(data, bags)
    l = real_len
    c = real_context

    while recv_data:
        if len(recv_data) >= 3000:
            i = random.randint(2, 100)
            yield recv_data[:i]
            recv_data = recv_data[i:]

        else:
            yield recv_data
            break


def data_divider(data: bytes, bags: int):
    res = b""
    b_len = []
    data_bags = []

    while bags:
        one_bag = random.randint(1, 64)

        if one_bag <= bags:
            data_bags.append(data * one_bag)
            bags += -one_bag
        else:
            data_bags.append(data * bags)
            bags = 0

    for bag in data_bags:
        length = struct.pack('i', len(bag))
        b_len.append(len(bag))

        res = b"".join([res, length, bag])

    return res, b_len, data_bags


class Client(object):

    def __init__(self):
        self._data_buf = buffer.Buffer()
        self._header_buf = buffer.Buffer(static=True, max_size=4)

    def get_data(self):
        """get data from server"""
        n = 0
        for data in data_creator(30000):

            while data:
                if len(data) >= 4:
                    if self._data_buf.is_empty and self._data_buf.size == -1:
                        if not self._header_buf.is_empty:
                            data = self._header_buf.put(data, errors="return")
                            self._data_buf.set_length(struct.unpack('i', self._header_buf.get())[0])
                            data = self._data_buf.put(data, errors="return")

                        else:
                            self._data_buf.set_length(struct.unpack('i', data[:4])[0])
                            data = data[4:]
                            data = self._data_buf.put(data, errors="return")

                    else:
                        data = self._data_buf.put(data, errors="return")

                    if self._data_buf.is_full:
                        j = self._data_buf.size
                        d = self._data_buf.get(reset_len=True)
                        assert d == c[n]
                        assert j == l[n]
                        n += 1

                    else:
                        break

                else:
                    if self._data_buf.is_empty and self._data_buf.size == -1:
                        self._header_buf.put(data)
                        data = b''

                    else:
                        data = self._data_buf.put(data, errors="return")

                        if self._data_buf.is_full:
                            j = self._data_buf.size
                            d = self._data_buf.get(reset_len=True)
                            assert d == c[n]
                            assert j == l[n]
                            n += 1


cl = Client()
cl.get_data()