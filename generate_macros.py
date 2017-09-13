#!/usr/bin/python3

import argparse

OUTPUT_FILENAME = 'SerializationMacros.hpp'

### Boilerplate Code Templates ###
pragma_once = '#pragma once\n'
serialize_begin =      '#define DEFAULT_SERIALIZE{count}({args_list}) std::size_t to_bytes(char* ret) const {{ \\\n'
to_bytes_first_line =  '        int bytes_written = mutils::to_bytes(a,ret);  \\\n'
to_bytes_middle_line = '        bytes_written += mutils::to_bytes({field},ret + bytes_written); \\\n'
to_bytes_return_line = '        return bytes_written + mutils::to_bytes({field},ret + bytes_written); \\\n'
to_bytes_one_field_return = '        return mutils::to_bytes(a, ret); \\\n'
closing_brace = '    } \\\n' # Not a format string template, so curly brace doesn't need to be doubled
bytes_size_begin = '    std::size_t bytes_size() const { \\\n'
bytes_size_line_begin = '        return'
bytes_size_line_part = ' mutils::bytes_size({field}) '
bytes_size_line_end = '; \\\n'
post_object_begin = '    void post_object(const std::function<void (char const * const, std::size_t)>&f ) const { \\\n'
post_object_line =  '        mutils::post_object(f,{field}); \\\n'
post_object_end =   '    } \n\n' # Ends both post_object and the macro definition
deserialize_begin = '#define DEFAULT_DESERIALIZE{count}(Name,{args_list}) \\\n'
from_bytes_begin = ('    static std::unique_ptr<Name> from_bytes(mutils::DeserializationManager* m, char const * buf){ \\\n'
                    '        auto a_obj = mutils::from_bytes<std::decay_t<decltype(a)> >(m, buf); \\\n')
declare_bytes_read = '        std::size_t bytes_read = mutils::bytes_size(*a_obj); \\\n'
from_bytes_mid_field = ('        auto {field}_obj = mutils::from_bytes<std::decay_t<decltype({field})> >(m, buf + bytes_read); \\\n'
                        '        bytes_read += mutils::bytes_size(*{field}_obj); \\\n')
from_bytes_last_field = ('        auto {field}_obj = mutils::from_bytes<std::decay_t<decltype({field})> >(m, buf + bytes_read); \\\n'
                         '        return std::make_unique<Name>({obj_ptrs_list}, '
                         '*(mutils::from_bytes<std::decay_t<decltype({last_field})> >(m, buf + bytes_read + mutils::bytes_size(*{field}_obj)))); \\\n')
from_bytes_one_field_return = '        return std::make_unique<Name>(*a_obj); \\\n'
from_bytes_two_fields_return = '        return std::make_unique<Name>(*a_obj, *(mutils::from_bytes<std::decay_t<decltype(b)> >(m, buf + mutils::bytes_size(*a_obj)))); \\\n'
from_bytes_end = '    } \n\n' # Ends both from_bytes and the macro definition

### Comment block that goes at the top of the file ###
header_comments = """
/**
 * This is an automatically-generated file that implements default serialization
 * support with a series of macros. Do not edit this file by hand; you should
 * generate it with generate_macros.py. The public interface is at the bottom of
 * the file.
 */

"""

### Complete snippet of code that goes at the end of the file ###
file_footer = r"""
#define DEFAULT_SERIALIZE_IMPL2(count, ...) DEFAULT_SERIALIZE ## count (__VA_ARGS__)
#define DEFAULT_SERIALIZE_IMPL(count, ...) DEFAULT_SERIALIZE_IMPL2(count, __VA_ARGS__)
#define DEFAULT_SERIALIZE(...) DEFAULT_SERIALIZE_IMPL(VA_NARGS(__VA_ARGS__), __VA_ARGS__)


#define DEFAULT_DESERIALIZE_IMPL2(count, ...) DEFAULT_DESERIALIZE ## count (__VA_ARGS__)
#define DEFAULT_DESERIALIZE_IMPL(count, ...) DEFAULT_DESERIALIZE_IMPL2(count, __VA_ARGS__)
#define DEFAULT_DESERIALIZE(...) DEFAULT_DESERIALIZE_IMPL(VA_NARGS(__VA_ARGS__), __VA_ARGS__)


/**
 * THIS (below) is the only user-facing macro in this file.
 * It's for automatically generating basic serialization support.
 * plop this macro inside the body of a class which extends 
 * ByteRepresentable, providing the name of the class (that you plopped this into)
 * as the first argument and the name of the class's fields as the remaining arguments.
 * Right now we only support up to seven fields; adding more support is easy, just ask if
 * you need.
 *
 * MAJOR CAVEAT: This macro assumes that there is a constructor
 * which takes all the class members (in the order listed). 
 * it's fine if this is a private constructor, but it needs to exist.
 * 
 */

#define DEFAULT_SERIALIZATION_SUPPORT(CLASS_NAME,CLASS_MEMBERS...)		\
        DEFAULT_SERIALIZE(CLASS_MEMBERS) DEFAULT_DESERIALIZE(CLASS_NAME,CLASS_MEMBERS)   \
    void ensure_registered(mutils::DeserializationManager&){}
"""


argparser = argparse.ArgumentParser(description='Generate ' + OUTPUT_FILENAME + \
        ' with support for the specified number of fields.')
argparser.add_argument('num_fields', metavar='N', type=int, help='The maximum number '
        'of serialized fields that the serialization macros should support (the ' 
        'larger the number, the more macros will be generated)')
args = argparser.parse_args()

with open(OUTPUT_FILENAME, 'w') as output:
    output.write(pragma_once) 
    output.write(header_comments)
    # First, generate the serializers
    for curr_num_fields in range(1,args.num_fields+1):
        field_vars = [chr(i) for i in range(ord('a'), ord('a')+curr_num_fields)]
        output.write(serialize_begin.format(count=curr_num_fields,
            args_list=','.join(field_vars)))
        # Write the "to_bytes" block
        if curr_num_fields > 1:
            output.write(to_bytes_first_line)
            for middle_line_count in range(1,curr_num_fields - 1):
                output.write(to_bytes_middle_line.format(field=field_vars[middle_line_count]))
            output.write(to_bytes_return_line.format(field=field_vars[-1]))
        else:
            # Special case for DEFAULT_SERIALIZE1
            output.write(to_bytes_one_field_return)
        output.write(closing_brace)
        # Write the "bytes_size" block
        output.write(bytes_size_begin)
        output.write(bytes_size_line_begin)
        output.write('+'.join([bytes_size_line_part.format(field=field_vars[fieldnum]) 
            for fieldnum in range(curr_num_fields)]))
        output.write(bytes_size_line_end)
        output.write(closing_brace)
        # Write the "post_object" block
        output.write(post_object_begin)
        for fieldnum in range(curr_num_fields):
            output.write(post_object_line.format(field=field_vars[fieldnum]))
        output.write(post_object_end)
    # Second, generate the deserializers
    for curr_num_fields in range(1, args.num_fields + 1):
        field_vars = [chr(i) for i in range(ord('a'), ord('a')+curr_num_fields)]
        output.write(deserialize_begin.format(count=curr_num_fields+1, 
            args_list=','.join(field_vars)))
        output.write(from_bytes_begin)
        if curr_num_fields == 1:
            output.write(from_bytes_one_field_return)
        elif curr_num_fields == 2:
            output.write(from_bytes_two_fields_return)
        else:
            output.write(declare_bytes_read)
            for fieldnum in range(1, curr_num_fields - 2):
                output.write(from_bytes_mid_field.format(field=field_vars[fieldnum]))
            output.write(from_bytes_last_field.format(field=field_vars[curr_num_fields-2], 
                last_field=field_vars[-1],
                obj_ptrs_list=','.join(['*' + var + '_obj' for var in field_vars[:-1]])))
        output.write(from_bytes_end)
    output.write(file_footer)


