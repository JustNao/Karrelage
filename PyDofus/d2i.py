#!/usr/bin/python3
# -*- coding: utf-8 -*-

import zlib, tempfile, io, unicodedata
from ._binarystream import _BinaryStream
from collections import OrderedDict

class InvalidD2IFile(Exception):
    def __init__(self, message):
        super(InvalidD2IFile, self).__init__(message)
        self.message = message

class D2I:
    def __init__(self, stream):
        self._stream = stream
        self._obj = OrderedDict()

    def read(self):
        raw = _BinaryStream(self._stream, True)

        indexs = OrderedDict()
        unDiacriticalIndex = OrderedDict()

        self._obj["texts"] = OrderedDict()
        self._obj["nameText"] = OrderedDict()
        self._obj["idText"] = OrderedDict()

        indexesPointer = raw.read_int32()
        self._stream.seek(indexesPointer)

        i = 0
        indexesLength = raw.read_int32()
        while i < indexesLength:
            key = raw.read_int32()
            diacriticalText = raw.read_bool()
            pointer = raw.read_int32()
            indexs[pointer] = key

            if diacriticalText:
                i += 4
                unDiacriticalIndex[key] = raw.read_int32()
            else:
                unDiacriticalIndex[key] = pointer
            i += 9

        indexesLength = raw.read_int32()
        while indexesLength > 0:
            position = self._stream.tell()
            textKey = raw.read_string().decode("utf-8")
            pointer = raw.read_int32()
            self._obj["nameText"][textKey] = indexs[pointer]
            indexesLength = (indexesLength - (self._stream.tell() - position))

        i = 0
        indexesLength = raw.read_int32()
        while indexesLength > 0:
            position = self._stream.tell()
            i += 1
            self._obj["idText"][raw.read_int32()] = i
            indexesLength = (indexesLength - (self._stream.tell() - position))

        for pointer, key in indexs.items():
            self._stream.seek(pointer)
            self._obj["texts"][key] = raw.read_string().decode("utf-8")

        return self._obj

    def write(self, obj):
        raw = _BinaryStream(self._stream, True)

        indexs = OrderedDict()

        raw.write_int32(0) # indexes offset

        i = 0
        for key in obj["texts"]:
            data = {"pointer": self._stream.tell(), "diacriticalText": False, }

            raw.write_string(obj["texts"][key].encode())
            if self.needCritical(obj["texts"][key]):
                data["diacriticalText"] = True
                data["unDiacriticalIndex"] = self._stream.tell()
                raw.write_string(self.unicode(obj["texts"][key].lower()))

            i += 1
            indexs[key] = data

        indexesSizePosition = self._stream.tell()
        raw.write_int32(0) # indexes size
        indexesPosition = self._stream.tell()

        for i, data in indexs.items():
            raw.write_int32(data["pointer"])
            raw.write_bool(data["diacriticalText"])
            raw.write_int32(data["pointer"])
            if data["diacriticalText"]:
                raw.write_int32(data["unDiacriticalIndex"])

        indexesLength = (self._stream.tell() - indexesPosition)

        nameTextSizePosition = self._stream.tell()
        raw.write_int32(0) # name text size
        nameTextPosition = self._stream.tell()

        for name, key in obj["nameText"].items():
            raw.write_string(name.encode())
            raw.write_int32(indexs[str(key)]["pointer"])

        nameTextLength = (self._stream.tell() - nameTextPosition)

        idTextSizePosition = self._stream.tell()
        raw.write_int32(0) # id text size
        idTextPosition = self._stream.tell()

        for id in obj["idText"]:
            raw.write_int32(int(id))

        idTextLength = (self._stream.tell() - idTextPosition)
        EOF = self._stream.tell()

        self._stream.seek(0)
        raw.write_int32(indexesSizePosition)

        self._stream.seek(indexesSizePosition)
        raw.write_int32(indexesLength)

        self._stream.seek(nameTextSizePosition)
        raw.write_int32(nameTextLength)

        self._stream.seek(idTextSizePosition)
        raw.write_int32(idTextLength)

        self._stream.seek(EOF)

    def needCritical(self, str):
        return all(ord(char) < 128 for char in str) == False

    def unicode(self, str):
        return unicodedata.normalize('NFD', str).encode('ascii', 'ignore')
