import src.parser as parser
import src.semantic_analizaer as check_semantic
from src.mips_generator import MIPS
from sys import argv
import subprocess
import src.cool2cil as cil

if __name__ == '__main__':
    if '-t' in argv:
        files = subprocess.Popen(['ls', 'examples/'], stdout=subprocess.PIPE).communicate()[0]
        files = files.decode()
        files = files.split('\n')
        files = list(filter(lambda x: len(x.split('.')) > 1 and x.split('.')[-1] == 'cl', files))
        print(files)
        for i in files:
            inp = ''
            with open(f'examples/{i}', 'r') as fd:
                temp = fd.read()
                while temp:
                    inp += temp
                    temp = fd.read()
            parser_object = parser.make_parser()
            ast = parser_object.parse(inp)
            semantic_object = check_semantic.CheckSemantic()
            cil_object = cil.Cool2cil()
            # try:
            scope_root = semantic_object.visit(ast, None)
            cil_object.visit(ast, scope_root)
            # mg = MIPS(cil_object)
            # mg.generate_mips()
            print(f'{i} ok')
            # except BaseException as e:
            #     print(f'{i} {e}')
    else:
        with open(f'{argv[1]}', 'r') as fd:
            inp = ''
            temp = fd.read()
            while temp:
                inp += temp
                temp = fd.read()
        parser_object = parser.make_parser()
        ast = parser_object.parse(inp)
        semantic_object = check_semantic.CheckSemantic()
        cil_object = cil.Cool2cil()
        scope_root = semantic_object.visit(ast, None)
        cil_object.visit(ast, scope_root)
        mips_object = MIPS(cil_object)
        mips_object.generate_mips()
        inp = ''
        with open('src/staticMipsCode.asm', 'r') as fd:
            temp = fd.read()
            while temp:
                inp += temp
                temp = fd.read()
        with open(f'{argv[2]}.asm', 'w') as fd:
            fd.write(inp)
            fd.write("\n")
            fd.write("# Start Mips Generated Code")
            fd.write("\n")
            for line in mips_object.mips_code:
                fd.write("\n" + line)