import sys
sys.path.append('../pylib')
from mysqlbinlog import *
from ctypes import *
import platform, time, re
from optparse import OptionParser


def print_updates(old, new):
    print('update')
    count, index = len(old), 0
    while index < count:
        print(old[index])
        print(new[index])
        index += 1


def print_inserts(rows):
    print('insert')
    for row in rows:
        print(row)

def print_deletes(rows):
    for row in rows:
        print(row)

def main(options, args):
    reader = BinLogReader(options.binlog)
    # TODO: reader?
    quit_when_eof = options.quit_when_eof
    milliseconds = options.milliseconds

    reg_list = []
    if options.ignore:
        ignore = options.ignore.replace('%', '\\w*').replace('.', '\\.')
        patterns = ignore.split(',')
        for pattern in patterns:
            reg = re.compile(pattern)
            reg_list.append(reg)

    event_header = EventHeader()

    count = 0
    skip = False
    while True:
        # print('-' * 30)
        h = reader.read_event_header(event_header)
        if not h:
            if quit_when_eof:
                break
            else:
                seconds = milliseconds / 1000
                time.sleep(seconds)
                continue
        
        event = reader.read_event(event_header)
        if skip:
            skip = False
            continue
        
        event_info = reader.read_event_info(event_header, event)
        if event_info.type_code == EventType.TABLE_MAP_EVENT:
            db, table = reader.read_table_map_event(event, event_info)
            full_name = db + '.' + table
            for reg in reg_list:
                if reg.match(full_name):
                    skip = True
                    # print('Skip', full_name)
                    break
            if skip:
                continue
            print('@', full_name)
        elif event_info.type_code == EventType.DELETE_ROWS_EVENT2:
            rows = reader.read_delete_event_rows(event, event_info)
            print_deletes(rows)
        elif event_info.type_code == EventType.UPDATE_ROWS_EVENT2:
            old, new = reader.read_update_event_rows(event, event_info)
            print_updates(old, new)
        elif event_info.type_code == EventType.WRITE_ROWS_EVENT2:
            rows = reader.read_insert_event_rows(event, event_info)
            print_inserts(rows)
            
        reader.free_event(event)
        count += 1
    
    reader.close()


if __name__ == '__main__':
    parser = OptionParser()

    parser.add_option("-s", "--source", action="store", dest="source", help="Provide source database")
    parser.add_option("-b", "--binlog", action="store", dest="binlog", help="Provide binlog file name")
    parser.add_option("-l", "--highlight", action="store", dest="highlight", help="Highlights the differences")
    parser.add_option("-i", "--ignore", action="store", dest="ignore", help="The db and table pattern to ignore")
    parser.add_option("-q", "--quit-when-eof", action="store", dest="quit_when_eof", help="Quit the program when EOF?", default=False)
    parser.add_option("-m", "--milliseconds", action="store", dest="milliseconds", help="Provide sleep seconds", default=10)
    options, args = parser.parse_args()
    
    if not options.binlog:
        print("binlog filename is required")
        exit()
    
    b = time.clock()
    main(options, args)
    e = time.clock()
    print('\nCost', e - b, 'seconds')