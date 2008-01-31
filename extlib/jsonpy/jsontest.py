import unittest

## Run the tests on minjson by changing the import...
import json
#import minjson as json

##    jsontest.py implements tests for the json.py JSON
##    (http://json.org) reader and writer.
##    Copyright (C) 2005  Patrick D. Logan
##    Contact mailto:patrickdlogan@stardecisions.com
##
##    This library is free software; you can redistribute it and/or
##    modify it under the terms of the GNU Lesser General Public
##    License as published by the Free Software Foundation; either
##    version 2.1 of the License, or (at your option) any later version.
##
##    This library is distributed in the hope that it will be useful,
##    but WITHOUT ANY WARRANTY; without even the implied warranty of
##    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
##    Lesser General Public License for more details.
##
##    You should have received a copy of the GNU Lesser General Public
##    License along with this library; if not, write to the Free Software
##    Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

# The object tests should be order-independent. They're not.
# i.e. they should test for existence of keys and values
# with read/write invariance.

def _removeWhitespace(str):
    return str.replace(" ", "")

class JsonTest(unittest.TestCase):
    def testReadEmptyObject(self):
        obj = json.read("{}")
        self.assertEqual({}, obj)

    def testWriteEmptyObject(self):
        s = json.write({})
        self.assertEqual("{}", _removeWhitespace(s))

    def testReadStringValue(self):
        obj = json.read('{ "name" : "Patrick" }')
        self.assertEqual({ "name" : "Patrick" }, obj)

    def testReadEscapedQuotationMark(self):
        obj = json.read(r'"\""')
        self.assertEqual(r'"', obj)

    def testReadEscapedSolidus(self):
        obj = json.read(r'"\/"')
        self.assertEqual(r'/', obj)

    def testReadEscapedReverseSolidus(self):
        obj = json.read(r'"\\"')
        self.assertEqual("\\", obj)

    def testReadEscapedBackspace(self):
        obj = json.read(r'"\b"')
        self.assertEqual("\b", obj)

    def testReadEscapedFormfeed(self):
        obj = json.read(r'"\f"')
        self.assertEqual("\f", obj)

    def testReadEscapedNewline(self):
        obj = json.read(r'"\n"')
        self.assertEqual("\n", obj)

    def testReadEscapedCarriageReturn(self):
        obj = json.read(r'"\r"')
        self.assertEqual("\r", obj)

    def testReadEscapedHorizontalTab(self):
        obj = json.read(r'"\t"')
        self.assertEqual("\t", obj)

    def testReadEscapedHexCharacter(self):
        obj = json.read(r'"\u000A"')
        self.assertEqual("\n", obj)
        obj = json.read(r'"\u1001"')
        self.assertEqual(u'\u1001', obj)

    def testWriteEscapedQuotationMark(self):
        s = json.write(r'"')
        self.assertEqual(r'"\""', _removeWhitespace(s))

    def testWriteEscapedSolidus(self):
        s = json.write(r'/', escaped_forward_slash=True)
        self.assertEqual(r'"\/"', _removeWhitespace(s))

    def testWriteNonEscapedSolidus(self):
        s = json.write(r'/')
        self.assertEqual(r'"/"', _removeWhitespace(s))

    def testWriteEscapedReverseSolidus(self):
        s = json.write("\\")
        self.assertEqual(r'"\\"', _removeWhitespace(s))

    def testWriteEscapedBackspace(self):
        s = json.write("\b")
        self.assertEqual(r'"\b"', _removeWhitespace(s))

    def testWriteEscapedFormfeed(self):
        s = json.write("\f")
        self.assertEqual(r'"\f"', _removeWhitespace(s))

    def testWriteEscapedNewline(self):
        s = json.write("\n")
        self.assertEqual(r'"\n"', _removeWhitespace(s))

    def testWriteEscapedCarriageReturn(self):
        s = json.write("\r")
        self.assertEqual(r'"\r"', _removeWhitespace(s))

    def testWriteEscapedHorizontalTab(self):
        s = json.write("\t")
        self.assertEqual(r'"\t"', _removeWhitespace(s))

    def testWriteEscapedHexCharacter(self):
        s = json.write(u'\u1001')
        self.assertEqual(u'"\u1001"', _removeWhitespace(s))

    def testReadBadEscapedHexCharacter(self):
        self.assertRaises(json.ReadException, self.doReadBadEscapedHexCharacter)

    def doReadBadEscapedHexCharacter(self):
        json.read('"\u10K5"')

    def testReadBadObjectKey(self):
        self.assertRaises(json.ReadException, self.doReadBadObjectKey)

    def doReadBadObjectKey(self):
        json.read('{ 44 : "age" }')

    def testReadBadArray(self):
        self.assertRaises(json.ReadException, self.doReadBadArray)

    def doReadBadArray(self):
        json.read('[1,2,3,,]')

    def testReadDoubleSolidusComment(self):
        obj = json.read("[1, 2, // This is a comment.\n 3]")
        self.assertEqual([1, 2, 3], obj)
        obj = json.read('[1, 2, // This is a comment.\n{"last":3}]')
        self.assertEqual([1, 2, {"last":3}], obj)

    def testReadBadDoubleSolidusComment(self):
        self.assertRaises(json.ReadException, self.doReadBadDoubleSolidusComment)

    def doReadBadDoubleSolidusComment(self):
        json.read("[1, 2, / This is not a comment.\n 3]")
        
    def testReadCStyleComment(self):
        obj = json.read("[1, 2, /* This is a comment. \n */ 3]")
        self.assertEqual([1, 2, 3], obj)
        obj = json.read('[1, 2, /* This is a comment. */{"last":3}]')
        self.assertEqual([1, 2, {"last":3}], obj)

    def testReadCStyleCommentWithoutEnd(self):
        self.assertRaises(json.ReadException, self.doReadCStyleCommentWithoutEnd)

    def testReadCStyleCommentWithSlashStar(self):
        self.assertRaises(json.ReadException, self.doReadCStyleCommentWithSlashStar)

    def doReadCStyleCommentWithoutEnd(self):
        json.read("[1, 2, /* This is not a comment./ 3]")

    def doReadCStyleCommentWithSlashStar(self):
        json.read("[1, 2, /* This is not a comment./* */ 3]")
        
    def testReadBadObjectSyntax(self):
        self.assertRaises(json.ReadException, self.doReadBadObjectSyntax)

    def doReadBadObjectSyntax(self):
        json.read('{"age", 44}')

    def testWriteStringValue(self):
        s = json.write({ "name" : "Patrick" })
        self.assertEqual('{"name":"Patrick"}', _removeWhitespace(s))

    def testReadIntegerValue(self):
        obj = json.read('{ "age" : 44 }')
        self.assertEqual({ "age" : 44 }, obj)

    def testReadNegativeIntegerValue(self):
        obj = json.read('{ "key" : -44 }')
        self.assertEqual({ "key" : -44 }, obj)
        
    def testReadFloatValue(self):
        obj = json.read('{ "age" : 44.5 }')
        self.assertEqual({ "age" : 44.5 }, obj)

    def testReadNegativeFloatValue(self):
        obj = json.read(' { "key" : -44.5 } ')
        self.assertEqual({ "key" : -44.5 }, obj)

    def testReadBadNumber(self):
        self.assertRaises(json.ReadException, self.doReadBadNumber)

    def doReadBadNumber(self):
        json.read('-44.4.4')

    def testReadSmallObject(self):
        obj = json.read('{ "name" : "Patrick", "age":44} ')
        self.assertEqual({ "age" : 44, "name" : "Patrick" }, obj)        

    def testReadEmptyArray(self):
        obj = json.read('[]')
        self.assertEqual([], obj)

    def testWriteEmptyArray(self):
        self.assertEqual("[]", _removeWhitespace(json.write([])))

    def testReadSmallArray(self):
        obj = json.read(' [ "a" , "b", "c" ] ')
        self.assertEqual(["a", "b", "c"], obj)

    def testWriteSmallArray(self):
        self.assertEqual('[1,2,3,4]', _removeWhitespace(json.write([1, 2, 3, 4])))

    def testWriteSmallObject(self):
        s = json.write({ "name" : "Patrick", "age": 44 })
        self.assertEqual('{"age":44,"name":"Patrick"}', _removeWhitespace(s))

    def testWriteFloat(self):
        self.assertEqual("3.445567", _removeWhitespace(json.write(3.44556677)))

    def testReadTrue(self):
        self.assertEqual(True, json.read("true"))

    def testReadFalse(self):
        self.assertEqual(False, json.read("false"))

    def testReadNull(self):
        self.assertEqual(None, json.read("null"))

    def testWriteTrue(self):
        self.assertEqual("true", _removeWhitespace(json.write(True)))

    def testWriteFalse(self):
        self.assertEqual("false", _removeWhitespace(json.write(False)))

    def testWriteNull(self):
        self.assertEqual("null", _removeWhitespace(json.write(None)))

    def testReadArrayOfSymbols(self):
        self.assertEqual([True, False, None], json.read(" [ true, false,null] "))

    def testWriteArrayOfSymbolsFromList(self):
        self.assertEqual("[true,false,null]", _removeWhitespace(json.write([True, False, None])))

    def testWriteArrayOfSymbolsFromTuple(self):
        self.assertEqual("[true,false,null]", _removeWhitespace(json.write((True, False, None))))

    def testReadComplexObject(self):
        src = '''
    { "name": "Patrick", "age" : 44, "Employed?" : true, "Female?" : false, "grandchildren":null }
'''
        obj = json.read(src)
        self.assertEqual({"name":"Patrick","age":44,"Employed?":True,"Female?":False,"grandchildren":None}, obj)

    def testReadLongArray(self):
        src = '''[    "used",
    "abused",
    "confused",
    true, false, null,
    1,
    2,
    [3, 4, 5]]
'''
        obj = json.read(src)
        self.assertEqual(["used","abused","confused", True, False, None,
                          1,2,[3,4,5]], obj)

    def testReadIncompleteArray(self):
        self.assertRaises(json.ReadException, self.doReadIncompleteArray)

    def doReadIncompleteArray(self):
        json.read('[')

    def testReadComplexArray(self):
        src = '''
[
    { "name": "Patrick", "age" : 44,
      "Employed?" : true, "Female?" : false,
      "grandchildren":null },
    "used",
    "abused",
    "confused",
    1,
    2,
    [3, 4, 5]
]
'''
        obj = json.read(src)
        self.assertEqual([{"name":"Patrick","age":44,"Employed?":True,"Female?":False,"grandchildren":None},
                          "used","abused","confused",
                          1,2,[3,4,5]], obj)

    def testWriteComplexArray(self):
        obj = [{"name":"Patrick","age":44,"Employed?":True,"Female?":False,"grandchildren":None},
               "used","abused","confused",
               1,2,[3,4,5]]
        self.assertEqual('[{"Female?":false,"age":44,"name":"Patrick","grandchildren":null,"Employed?":true},"used","abused","confused",1,2,[3,4,5]]',
                         _removeWhitespace(json.write(obj)))


    def testReadWriteCopies(self):
        orig_obj = {'a':' " '}
        json_str = json.write(orig_obj)
        copy_obj = json.read(json_str)
        self.assertEqual(orig_obj, copy_obj)
        self.assertEqual(True, orig_obj == copy_obj)
        self.assertEqual(False, orig_obj is copy_obj)

    def testStringEncoding(self):
        s = json.write([1, 2, 3])
        self.assertEqual(unicode("[1,2,3]", "utf-8"), _removeWhitespace(s))

    def testReadEmptyObjectAtEndOfArray(self):
        self.assertEqual(["a","b","c",{}],
                         json.read('["a","b","c",{}]'))

    def testReadEmptyObjectMidArray(self):
        self.assertEqual(["a","b",{},"c"],
                         json.read('["a","b",{},"c"]'))

    def testReadClosingObjectBracket(self):
        self.assertEqual({"a":[1,2,3]}, json.read('{"a":[1,2,3]}'))

    def testAnotherDoubleSlashComment(self):
        obj = json.read('[1 , // xzy\n2]')
        self.assertEqual(obj, [1, 2])

    def testAnotherSlashStarComment(self):
        obj = json.read('[1,/* xzy */2]')
        self.assertEqual(obj, [1, 2])

    def testEmptyObjectInList(self):
        obj = json.read('[{}]')
        self.assertEqual([{}], obj)

    def testObjectInListWithSlashStarComment(self):
        obj1 = json.read('[{} /*Comment*/]')
        self.assertEqual([{}], obj1)

    def testObjectWithEmptyList(self):
        obj = json.read('{"test": [] }')
        self.assertEqual({"test":[]}, obj)

    def testObjectWithNonEmptyList(self):
        obj = json.read('{"test": [3, 4, 5] }')
        self.assertEqual({"test":[3, 4, 5]}, obj)

    def testCommentInObjectWithListValue(self):
        obj2 = json.read('{"test": [] /*Comment*/}')
        self.assertEqual({"test":[]}, obj2)

    def testWriteLong(self):
        self.assertEqual("12345678901234567890", json.write(12345678901234567890))
        
def main():
    unittest.main()

if __name__ == '__main__':
    main()
