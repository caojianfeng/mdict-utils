import os.path
import argparse

from . import about
from . import reader
from .writer import pack, pack_mdd_file, pack_mdx_txt, pack_mdx_sqlite3,  \
    txt2sqlite, sqlite2txt
from .utils import ElapsedTimer


total = 0


def make_callback(fmt):
    def callback(value):
        global total
        total += value
        print(fmt % total, end='')
    return callback


def run():
    epilog = ''
    parser = argparse.ArgumentParser(prog='mdict', description=about.description, epilog=epilog)
    parser.add_argument('--version', action='version',
                        version='%%(prog)s version %s - written by %s <%s>' % (
                            about.version, about.author, about.email),
                        help='show version')
    parser.add_argument('-k', dest='key', action='store_true', help='show mdx/mdd keys')
    parser.add_argument('-m', dest='meta', action='store_true', help='show mdx/mdd meta information')
    parser.add_argument('-q', dest='query', metavar='<key>', help='query KEY from mdx/mdd')
    parser.add_argument('--txt-db', action='store_true', help='convert mdx txt to sqlite3 db. <mdx/mdd> is ".txt"')
    parser.add_argument('--db-txt', action='store_true', help='convert sqlite3 db to mdx txt. <mdx/mdd> is ".db"')
    parser.add_argument('mdict', metavar='<mdx/mdd>', help='Dictionary MDX/MDD file')

    group = parser.add_argument_group('Reader')
    group.add_argument('-x', dest='extract', action='store_true', help='extract mdx/mdd file.')
    group.add_argument('-d', dest='exdir', help='extracted directory')
    group.add_argument('--mdict-db', action='store_true', help='extract mdict to DB')
    group.add_argument('--split-n', metavar='<number>', help='split MDX TXT to N files')
    group.add_argument('--split-az', action='store_true', help='split MDX TXT to files by a...z')

    group = parser.add_argument_group('Writer')
    group.add_argument('-a', dest='add', metavar='<resource>', action='append', help='add resource file to mdx/mdd file')
    group.add_argument('--title', metavar='<title>', help='Dictionary title file')
    group.add_argument('--description', metavar='<description>', help='Dictionary descritpion file')
    group.add_argument('--encoding', metavar='<encoding>', default='utf-8', help='mdx txt file encoding')

    args = parser.parse_args()

    global total

    if args.meta:
        with ElapsedTimer(verbose=True):
            meta = reader.meta(args.mdict)
            print('Title: %(title)s' % meta)
            print('Engine Version: %(generatedbyengineversion)s' % meta)
            'record' in meta and print('Record: %(record)s' % meta)
            print('Format: %(format)s' % meta)
            'encoding' in meta and print('Encoding: %(encoding)s' % meta)
            'creationdate' in meta and print('Creation Date: %(creationdate)s' % meta)
            print('Description: %(description)s' % meta)
    elif args.key:
        keys = reader.get_keys(args.mdict)
        count = 0
        for key in keys:
            count += 1
            key = key.decode('utf-8')
            print(key)
    elif args.txt_db:
        with ElapsedTimer(verbose=True):
            total = 0
            fmt = '\rConvert "%s": %%s' % args.mdict
            txt2sqlite(args.mdict, callback=make_callback(fmt))
            print()
    elif args.db_txt:
        with ElapsedTimer(verbose=True):
            total = 0
            fmt = '\rConvert "%s": %%s' % args.mdict
            sqlite2txt(args.mdict, callback=make_callback(fmt))
            print()
    elif args.query:
        with ElapsedTimer(verbose=True):
            record = reader.query(args.mdict, args.query)
            print(record)
    elif args.extract:
        with ElapsedTimer(verbose=True):
            if args.mdict_db:
                reader.unpack_to_db(args.mdict)
            else:
                if args.split_az:
                    split = 'az'
                elif args.split_n:
                    split = args.split_n
                else:
                    split = None
                reader.unpack(args.exdir, args.mdict, split=split)
    elif args.add:
        with ElapsedTimer(verbose=True):
            is_mdd = args.mdict.endswith('.mdd')
            dictionary = []
            for resource in args.add:
                fmt = '\rScan "%s": %%s' % resource
                total = 0
                if is_mdd:
                    d = pack_mdd_file(resource, callback=make_callback(fmt))
                elif resource.endswith('.db'):
                    d = pack_mdx_sqlite3(resource, encoding=args.encoding, callback=make_callback(fmt))
                else:
                    d = pack_mdx_txt(resource, encoding=args.encoding, callback=make_callback(fmt))
                dictionary.extend(d)
                print()
            print()
            title = ''
            description = ''
            if args.title:
                title = open(args.title, 'rt').read()
            if args.description:
                description = open(args.description, 'rt').read()
            print('Pack to "%s"' % args.mdict)
            pack(args.mdict, dictionary, title, description, encoding=args.encoding, is_mdd=is_mdd)
    else:
        parser.print_help()


if __name__ == '__main__':
    run()
