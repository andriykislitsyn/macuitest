"""Convert from common Python types to Apple Event Manager types and vice-versa."""

import datetime
import struct

from Foundation import NSAppleEventDescriptor, NSURL

from . import kae

__all__ = ['Codecs', 'AEType', 'AEEnum', 'four_characters_code']


def four_characters_code(code):
    """ Convert four-char code for use in NSAppleEventDescriptor methods.

        code : bytes -- four-char code, e.g. b'utxt'
        Result : int -- OSType, e.g. 1970567284
    """
    return struct.unpack('>I', code)[0]


class Codecs:
    """ Implements mappings for common Python types with direct AppleScript equivalents. Used by AppleScript class. """

    kMacEpoch = datetime.datetime(1904, 1, 1)
    kUSRF = four_characters_code(kae.keyASUserRecordFields)

    def __init__(self):
        # Clients may add/remove/replace encoder and decoder items:
        self.encoders = {
            NSAppleEventDescriptor.class__(): self.pack_description,
            type(None): self.pack_none,
            bool: self.pack_bool,
            int: self.pack_int,
            float: self.pack_float,
            bytes: self.pack_bytes,
            str: self.pack_str,
            list: self.pack_list,
            tuple: self.pack_list,
            dict: self.pack_dict,
            datetime.datetime: self.pack_datetime,
            AEType: self.pack_type,
            AEEnum: self.pack_enum,
        }

        self.decoders = {four_characters_code(k): v for k, v in {
            kae.typeNull: self.unpack_null,
            kae.typeBoolean: self.unpack_boolean,
            kae.typeFalse: self.unpack_boolean,
            kae.typeTrue: self.unpack_boolean,
            kae.typeSInt32: self.unpack_s_int32,
            kae.typeIEEE64BitFloatingPoint: self.unpack_float64,
            kae.typeUTF8Text: self.unpack_unicode_text,
            kae.typeUTF16ExternalRepresentation: self.unpack_unicode_text,
            kae.typeUnicodeText: self.unpack_unicode_text,
            kae.typeLongDateTime: self.unpack_long_datetime,
            kae.typeAEList: self.unpack_ae_list,
            kae.typeAERecord: self.unpack_ae_record,
            kae.typeAlias: self.unpack_file,
            kae.typeFSS: self.unpack_file,
            kae.typeFSRef: self.unpack_file,
            kae.typeFileURL: self.unpack_file,
            kae.typeType: self.unpack_type,
            kae.typeEnumeration: self.unpack_enumeration,
        }.items()}

    def pack(self, data):
        """Pack Python data.
            data : anything -- a Python value
            Result : NSAppleEventDescriptor -- an AE descriptor, or error if no encoder exists for this type_ of data
        """
        try:
            return self.encoders[data.__class__](data)  # quick lookup by type_/class
        except (KeyError, AttributeError):
            for type_, encoder in self.encoders.items():
                # slower but more thorough lookup that can handle subtypes/subclasses
                if isinstance(data, type_):
                    return encoder(data)
        raise TypeError("Can't pack data into an AEDesc (unsupported type_): {!r}".format(data))

    def unpack(self, desc):
        """Unpack an Apple event descriptor.
            desc : NSAppleEventDescriptor
            Result : anything -- a Python value, or the original NSAppleEventDescriptor if no decoder is found
        """
        decoder = self.decoders.get(desc.descriptorType())
        # unpack known type
        if decoder:
            return decoder(desc)
        # if it's a record-like desc, unpack as dict with an extra AEType(b'pcls') key containing the desc type
        rec = desc.coerceToDescriptorType_(four_characters_code(kae.typeAERecord))
        if rec:
            rec = self.unpack_ae_record(rec)
            rec[AEType(kae.pClass)] = AEType(struct.pack('>I', desc.descriptorType()))
            return rec
        # return as-is
        return desc

    @staticmethod
    def _pack_bytes(description_type, data):
        return NSAppleEventDescriptor.descriptorWithDescriptorType_bytes_length_(
            four_characters_code(description_type), data, len(data))

    @staticmethod
    def pack_description(val):
        return val

    @staticmethod
    def pack_none():
        return NSAppleEventDescriptor.nullDescriptor()

    @staticmethod
    def pack_bool(val):
        return NSAppleEventDescriptor.descriptorWithBoolean_(int(val))

    def pack_int(self, val):
        if (-2 ** 31) <= val < (2 ** 31):
            return NSAppleEventDescriptor.descriptorWithInt32_(val)
        else:
            return self.pack(float(val))

    def pack_float(self, val):
        return self._pack_bytes(kae.typeFloat, struct.pack('d', val))

    def pack_bytes(self, val):
        return self._pack_bytes(kae.typeData, val)

    @staticmethod
    def pack_str(val):
        return NSAppleEventDescriptor.descriptorWithString_(val)

    def pack_datetime(self, val):
        delta = val - self.kMacEpoch
        sec = delta.days * 3600 * 24 + delta.seconds
        return self._pack_bytes(kae.typeLongDateTime, struct.pack('q', sec))

    def pack_list(self, val):
        lst = NSAppleEventDescriptor.listDescriptor()
        for item in val:
            lst.insertDescriptor_atIndex_(self.pack(item), 0)
        return lst

    def pack_dict(self, val):
        record = NSAppleEventDescriptor.recordDescriptor()
        usrf = desctype = None
        for key, value in val.items():
            if isinstance(key, AEType):
                if key.code == kae.pClass and isinstance(value, AEType):
                    # AS packs records that contain a 'class' property by coercing the packed record
                    # to the descriptor type specified by the property's value (assuming it's an AEType)
                    desctype = value
                else:
                    record.setDescriptor_forKeyword_(self.pack(value), four_characters_code(key.code))
            else:
                if not usrf:
                    usrf = NSAppleEventDescriptor.listDescriptor()
                usrf.insertDescriptor_atIndex_(self.pack(key), 0)
                usrf.insertDescriptor_atIndex_(self.pack(value), 0)
        if usrf:
            record.setDescriptor_forKeyword_(usrf, self.kUSRF)
        if desctype:
            new_record = record.coerceToDescriptorType_(four_characters_code(desctype.code))
            if new_record:
                record = new_record
            else:  # coercion failed for some reason, so pack as normal key-value pair
                # noinspection PyUnboundLocalVariable
                record.setDescriptor_forKeyword_(self.pack(desctype), four_characters_code(key.code))
        return record

    @staticmethod
    def pack_type(val):
        return NSAppleEventDescriptor.descriptorWithTypeCode_(four_characters_code(val.code))

    @staticmethod
    def pack_enum(val):
        return NSAppleEventDescriptor.descriptorWithEnumCode_(four_characters_code(val.code))

    @staticmethod
    def unpack_null(desc):
        _ = desc
        return None

    @staticmethod
    def unpack_boolean(desc):
        return desc.booleanValue()

    @staticmethod
    def unpack_s_int32(desc):
        return desc.int32Value()

    @staticmethod
    def unpack_float64(desc):
        return struct.unpack('d', bytes(desc.data()))[0]

    @staticmethod
    def unpack_unicode_text(desc):
        return desc.stringValue()

    def unpack_long_datetime(self, desc):
        return self.kMacEpoch + datetime.timedelta(seconds=struct.unpack('q', bytes(desc.data()))[0])

    def unpack_ae_list(self, desc):
        return [self.unpack(desc.descriptorAtIndex_(i + 1)) for i in range(desc.numberOfItems())]

    def unpack_ae_record(self, desc):
        dct = {}
        for i in range(desc.numberOfItems()):
            key = desc.keywordForDescriptorAtIndex_(i + 1)
            value = desc.descriptorForKeyword_(key)
            if key == self.kUSRF:
                lst = self.unpack_ae_list(value)
                # noinspection PyAssignmentToLoopOrWithParameter
                for i in range(0, len(lst), 2):
                    dct[lst[i]] = lst[i + 1]
            else:
                dct[AEType(struct.pack('>I', key))] = self.unpack(value)
        return dct

    @staticmethod
    def unpack_type(desc):
        return AEType(struct.pack('>I', desc.typeCodeValue()))

    @staticmethod
    def unpack_enumeration(desc):
        return AEEnum(struct.pack('>I', desc.enumCodeValue()))

    @staticmethod
    def unpack_file(desc):
        url = bytes(desc.coerceToDescriptorType_(four_characters_code(kae.typeFileURL)).data()).decode('utf8')
        return NSURL.URLWithString_(url).path()


class AETypeBase:
    """
        Base class for AEType and AEEnum.
        Hashable and comparable, so may be used as keys in dictionaries that map to AE records.
    """
    def __init__(self, code: bytes):
        if not isinstance(code, bytes):
            raise TypeError('invalid code (not a bytes object): {!r}'.format(code))
        elif len(code) != 4:
            raise ValueError('invalid code (not four bytes long): {!r}'.format(code))
        self._code = code

    code = property(lambda self: self._code, doc="bytes -- four-char code, e.g. b'utxt'")

    def __hash__(self):
        return hash(self._code)

    def __eq__(self, val):
        return val.__class__ == self.__class__ and val.code == self._code

    def __ne__(self, val):
        return not self == val

    def __repr__(self):
        return "{}({!r})".format(self.__class__.__name__, self._code)


class AEType(AETypeBase):
    """An AE type. Maps to an AppleScript type class, e.g. AEType(b'utxt') <=> 'unicode text'."""


class AEEnum(AETypeBase):
    """An AE enumeration. Maps to an AppleScript constant, e.g. AEEnum(b'yes ') <=> 'yes'."""
