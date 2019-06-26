import src.ast as ast
import src.cil_nodes as cil_node
import src.visitor as visitor
import src.scope as Scope
from src.scope import Scope
from src.type import ctype


class vTable:
    """
    {type:{f_name: int}}
    """
    pass


BACKUP_REGISTER = 't0'


class CILScope:
    def __init__(self, classname, parentScope=None):
        self.classname = classname
        self.parentScope = parentScope
        self.vars = []

    def add_var(self, var):
        self.vars.append(var)

    def get_real_name(self, var_name: str):
        for name in self.vars:
            if var_name in name:
                return name
        if self.parentScope:
            return self.parentScope.get_real_name(var_name)
        return ''


class Unique_name_generator:
    def __init__(self):
        self.name_keys = {}

    def generate(self, var: str, just_int=False):
        value = 1
        if var in self.name_keys:
            self.name_keys[var] += 1
            value = self.name_keys[var]
        else:
            self.name_keys[var] = 1
        if just_int:
            return value
        return f'{var}@{str(value)}'

    def reset(self):
        self.name_keys = {}


class Cool2cil:

    def _build_tree(self, scope):
        t = scope.get_types().copy()
        t.pop('SELF_TYPE')
        tree = {i: [] for i in t}
        for i in t:
            if t[i].parent:
                tree[t[i].parent.name] += [t[i].name]
        return tree

    def dfs(self, ty):
        t = {x: [-1, -1] for x in ty}
        self._dfs('Object', ty, 0, t)
        return t

    def _dfs(self, node, dic_type, time, tree):
        tree[node][0] = time
        n_t = time + 1
        for i in dic_type[node]:
            n_t = self._dfs(i, dic_type, n_t, tree)
        tree[node][1] = n_t
        return n_t + 1

    def calc_static(self, type):
        for i in self.dtpe:
            if i.cType == type:
                return len(i.attributes)

    def sort_type(self, type_list: dict):
        type_list = list(type_list.values())
        type_map = {}
        bit_mask = [False] * len(type_list)
        for i in range(len(type_list)):
            ctype = type_list[i]
            type_map[ctype.name] = i

        bit_mask[type_map['Object']] = True
        sorted = {}
        self_type = type_list[type_map['SELF_TYPE']]
        sorted[self_type.name] = self_type
        object_type = type_list[type_map['Object']]
        sorted[object_type.name] = object_type
        for i in range(len(type_list)):
            ctype = type_list[i]
            if ctype.name == 'Object' or ctype.name == 'SELF_TYPE':
                continue
            if not bit_mask[i]:
                self.sort_type_(ctype, type_list, type_map, bit_mask, sorted)
        return sorted

    def sort_type_(self, ctype, type_list, type_map, mask, sort_list):
        mask[type_map[ctype.name]] = True
        parent = ctype.parent
        iparent = type_map[parent.name]
        if not mask[iparent]:
            self.sort_type_(parent, type_list, type_map, mask, sort_list)
        sort_list[ctype.name] = ctype

    def get_node_by_type(self, t, classes):
        for i in classes:
            if t == i.name:
                return i

    def replace(self, method, tp):
        t = []
        rep = False
        for i in range(len(tp.methods)):
            if (list(method.keys())[0]).split('.')[1] != (list(tp.methods[i].keys())[0]).split('.')[1]:
                t.append(tp.methods[i])
            else:
                rep = True
                t.append(method)
        if not rep:
            t.append(method)
        tp.methods = t

    def __init__(self):
        self.tree = None
        self.constructors = {}
        self.data = []
        self.dtpe = []
        self.code = []
        self.vtable = vTable()
        self.name_generator = Unique_name_generator()
        self.keys_generator = Unique_name_generator()

    def _dispatch(self, ctype, method):
        for i in self.dtpe:
            if i.cType == ctype:
                for j in range(len(i.methods)):
                    if i.methods[j].split('.')[1] == method:
                        return j

    def _att_offset(self, ct, att):
        for i in self.dtpe:
            if i.cType == ct:
                for j in range(len(i.attributes)):
                    if i.attributes[j] == att:
                        return j

    @visitor.on('node')
    def visit(self, node, scope):
        pass

    @visitor.when(ast.Program)
    def visit(self, node: ast.Program, _):
        scope_root = Scope(None, None)
        for classDef in node.classes:
            new_type = ctype(classDef.name)
            scope_root.createType(new_type)
        for classDef in node.classes:
            a = scope_root.getType(classDef.name)
            a.parent = scope_root.getType(classDef.parent)
        new_types = self.sort_type(scope_root.get_types())
        node.classes = list(map(lambda x: self.get_node_by_type(x, node.classes), list(new_types.keys())[6:]))
        scope_root.set_types(new_types)
        t = scope_root.get_types()
        self.tree = self._build_tree(scope_root)
        self.tree = self.dfs(self.tree)
        for i in list(new_types.keys())[1:6]:
            new_types[i].fix_methods()
            tp = new_types[i].methods
            if i != 'Object':
                new_types[i].methods = []
                new_types[i].add_method(*tuple(new_types['Object'].methods + tp))

        for j in node.classes:
            scope = Scope(j.name, scope_root)
            methods = filter(lambda x: type(x) is ast.ClassMethod, j.features)
            methods = list(methods)
            attribs = filter(lambda x: type(x) is ast.ClassAttribute, j.features)
            attribs = list(attribs)
            p_type = scope.getType(j.parent)
            scope.getType(j.name).add_method(*tuple(scope.getType('Object').methods))
            scope.getType(j.name).add_attrib(*tuple(p_type.attributes))
            for i in p_type.methods:
                self.replace(i, scope.getType(j.name))
            for i in attribs:
                scope.getType(j.name).add_attrib({i.name: scope.getType(i.attr_type)})
            for i in methods:
                m = {f'{j.name}.{i.name}': {
                    'formal_params': {
                        t.name: scope.getType(t.param_type) for t in i.formal_params
                    },
                    'return_type': scope.getType(i.return_type),
                    'body': i.body
                }}
                self.replace(m, scope.getType(j.name))
        for i in list(t.keys())[1:]:
            self.constructors[i] = []
            meths = []
            for m in t[i].methods:
                meths.append(list(m.keys())[0])
            attrs = []
            for a in t[i].attributes:
                attrs.append(list(a.keys())[0])
            t1 = self.tree[t[i].name]
            self.dtpe.append(cil_node.DotType(t[i].name, attrs, meths, t1[0], t1[1]))

        self.constructors['Int'].append(cil_node.CILAttribute('#', [cil_node.CILInteger(0)], []))
        self.constructors['Bool'].append(cil_node.CILAttribute('#', [cil_node.CILBoolean(0)], []))
        self.constructors['String'].append(cil_node.CILAttribute('#', [cil_node.CILString(0)], []))
        self.dtpe[1].attributes.append('#')
        self.dtpe[2].attributes.append('#')
        self.dtpe[3].attributes.append('#')
        for i in node.classes:
            self.visit(i, None)

    @visitor.when(ast.Class)
    def visit(self, node: ast.Class, scope: CILScope):
        attrs = filter(lambda x: type(x) is ast.ClassAttribute, node.features)
        attrs = list(attrs)
        for attr in attrs:
            self.constructors[node.name] += (self.visit(attr, CILScope(node.name))[1])
        methods = filter(lambda x: type(x) is ast.ClassMethod, node.features)
        methods = list(methods)
        for method in methods:
            self.visit(method, CILScope(node.name))

    @visitor.when(ast.ClassMethod)
    def visit(self, node: ast.ClassMethod, scope: CILScope):
        self.name_generator.reset()
        params = ['self']
        for p in node.formal_params:
            redefinition = self.name_generator.generate(p.name)
            params.append(redefinition)
            scope.add_var(redefinition)
        var, exprs = self.visit(node.body, scope)
        method = cil_node.CILMethod(node.name, scope.classname, params, var, exprs)
        self.code.append(method)

    @visitor.when(ast.Assignment)
    def visit(self, node: ast.Assignment, scope: CILScope):
        real_name = scope.get_real_name(node.instance.name)
        expr = self.visit(node.expr, scope)
        if real_name == '':
            assignment_node = cil_node.CILSetAttr(self._att_offset(scope.classname, node.instance.name))
        else:
            assignment_node = cil_node.CILAssignment(real_name)
        return expr[0], expr[1] + [assignment_node]

    @visitor.when(ast.Block)
    def visit(self, node: ast.Block, scope: CILScope):
        var = []
        codes = []
        for expr in node.expr_list:
            tmp = self.visit(expr, scope)
            var += tmp[0]
            codes += tmp[1]
        codes.append(cil_node.CILBlock(len(node.expr_list)))
        return var, codes

    @visitor.when(ast.DynamicDispatch)
    def visit(self, node: ast.DynamicDispatch, scope: CILScope):
        args = []
        var = []
        codes = []
        for item in node.arguments:
            tmp = self.visit(item, scope)
            codes += tmp[1]
            if item.static_type.name in ['Int', 'Bool']:
                codes += [cil_node.CILDynamicDispatch(0, self._dispatch(item.static_type.name, "copy"))]
        tmp = self.visit(node.instance, scope)
        codes += tmp[1]
        t = node.instance.static_type.name
        if t == 'SELF_TYPE':
            t = scope.classname
        codes.append(cil_node.CILDynamicDispatch(len(node.arguments), self._dispatch(t, node.method)))
        return var, codes

    @visitor.when(ast.StaticDispatch)
    def visit(self, node: ast.StaticDispatch, scope: CILScope):
        args = []
        var = []
        codes = []
        for item in node.arguments:
            tmp = self.visit(item, scope)
            codes += tmp[1]
            if item.static_type.name in ['Int', 'Bool']:
                codes += [cil_node.CILDynamicDispatch(0, self._dispatch(item.static_type.name, "copy"))]
        tmp = self.visit(node.instance, scope)
        codes += tmp[1]
        codes.append(cil_node.CILStaticDispatch(len(node.arguments), node.dispatch_type, node.method))
        return var, codes

    @visitor.when(ast.ClassAttribute)
    def visit(self, node: ast.ClassAttribute, scope):
        if node.init_expr:
            tmp = self.visit(node.init_expr, scope)
            return tmp[0], [cil_node.CILAttribute(node.name, tmp[1], tmp[0])]
        if node.static_type.name in ['String', 'Int', 'Bool']:
            return [], [cil_node.CILAttribute(node.name, [
                cil_node.CILInteger(0) if node.static_type.name != 'String' else cil_node.CILNewString() 
            ], [])]
        return [], []

    @visitor.when(ast.NewObject)
    def visit(self, node: ast.NewObject, scope):
        c = self.constructors[node.static_type.name]
        t = []
        att = []
        for i in c:
            t += i.exp_code
            t.append(cil_node.CILInitAttr(self._att_offset(node.static_type.name, i.offset), i.scope))
            att += i.scope
        return [], [cil_node.CILNew(t, node.type, self.calc_static(node.static_type.name), att)]

    @visitor.when(ast.Integer)
    def visit(self, node: ast.Integer, scope):
        return [], [cil_node.CILInteger(node.content)]

    @visitor.when(ast.Boolean)
    def visit(self, node: ast.Boolean, scope):
        value = 1 if node.content else 0
        return [], [cil_node.CILBoolean(value)]

    @visitor.when(ast.String)
    def visit(self, node: ast.String, scope):
        self.data.append(node.content)
        return [], [cil_node.CILString(len(self.data)-1)]

    @visitor.when(ast.Addition)
    def visit(self, node: ast.Addition, scope):
        fst = self.visit(node.first, scope)
        snd = self.visit(node.second, scope)
        return fst[0] + snd[0], [cil_node.CILArithm(fst[1], snd[1], '+')]

    @visitor.when(ast.Subtraction)
    def visit(self, node: ast.Subtraction, scope):
        fst = self.visit(node.first, scope)
        snd = self.visit(node.second, scope)
        return fst[0] + snd[0], [cil_node.CILArithm(fst[1], snd[1], '-')]

    @visitor.when(ast.Multiplication)
    def visit(self, node: ast.Multiplication, scope):
        fst = self.visit(node.first, scope)
        snd = self.visit(node.second, scope)
        return fst[0] + snd[0], [cil_node.CILArithm(fst[1], snd[1], '*')]

    @visitor.when(ast.Division)
    def visit(self, node: ast.Division, scope):
        fst = self.visit(node.first, scope)
        snd = self.visit(node.second, scope)
        return fst[0] + snd[0], [cil_node.CILArithm(fst[1], snd[1], '/')]

    @visitor.when(ast.Equal)
    def visit(self, node: ast.Equal, scope):
        fst = self.visit(node.first, scope)
        snd = self.visit(node.second, scope)
        if node.first.static_type.name in ['Int', 'Bool']:
            return fst[0] + snd[0], [cil_node.CILEq(fst[1], snd[1])]
        if node.first.static_type.name == 'String':
            return fst[0] + snd[0], [cil_node.CILEqString(fst[1], snd[1])]
        return fst[0] + snd[0], [cil_node.CILEqObject(fst[1], snd[1])]

    @visitor.when(ast.LessThan)
    def visit(self, node: ast.LessThan, scope):
        fst = self.visit(node.first, scope)
        snd = self.visit(node.second, scope)
        return fst[0] + snd[0], [cil_node.CILBoolOp(fst[1], snd[1], '<')]

    @visitor.when(ast.LessThanOrEqual)
    def visit(self, node: ast.LessThanOrEqual, scope):
        fst = self.visit(node.first, scope)
        snd = self.visit(node.second, scope)
        return fst[0] + snd[0], [cil_node.CILBoolOp(fst[1], snd[1], '<=')]

    @visitor.when(ast.IntegerComplement)
    def visit(self, node: ast.IntegerComplement, scope):
        t = self.visit(node.integer_expr, scope)
        return t[0], [cil_node.CILNArith(t[1])]

    @visitor.when(ast.BooleanComplement)
    def visit(self, node: ast.BooleanComplement, scope):
        t = self.visit(node.boolean_expr, scope)
        return t[0], [cil_node.CILNBool(t[1])]

    @visitor.when(ast.Let)
    def visit(self, node: ast.Let, scope: CILScope):
        new_scope = CILScope(scope.classname, scope)
        var = []
        codes = []
        for item in node.declarations:
            tmp = self.visit(item, new_scope)
            var += tmp[0]
            codes += tmp[1]
        tmp = self.visit(node.body, new_scope)
        var += tmp[0]
        codes += tmp[1]
        return var, codes

    @visitor.when(ast.Formal)
    def visit(self, node: ast.Formal, scope: CILScope):
        new_name = self.name_generator.generate(node.name)
        scope.add_var(new_name)
        var = [new_name]
        codes = []
        if node.init_expr:
            tmp = self.visit(node.init_expr, scope)
            var += tmp[0]
            codes += tmp[1]
            codes.append(cil_node.CILFormal(new_name))
        elif node.static_type.name in ['Bool', 'Int', 'String']:
            # c = self.constructors[node.static_type.name]
            # t = []
            # for i in c:
            #     t += i.exp_code
            #     t.append(cil_node.CILInitAttr(self._att_offset(node.static_type.name, i.offset),i.scope))
            codes = [
                cil_node.CILNew([], node.static_type.name, self.calc_static(node.static_type.name), []), cil_node.CILFormal(new_name)
            ] if node.static_type.name != 'String' else [
                cil_node.CILNewString(), cil_node.CILFormal(new_name)
            ]
        else:
            codes = [cil_node.CILFormal(new_name, False)]
        return var, codes

    @visitor.when(ast.If)
    def visit(self, node: ast.If, scope: CILScope):
        predicate_visit = self.visit(node.predicate, scope)
        if_visit = self.visit(node.then_body, scope)
        else_visit = self.visit(node.else_body, scope)
        int_key = self.keys_generator.generate('if', True)
        return predicate_visit[0] + if_visit[0] + else_visit[0], \
               [cil_node.CILIf(predicate_visit[1], if_visit[1], else_visit[1], int_key)]

    @visitor.when(ast.WhileLoop)
    def visit(self, node: ast.WhileLoop, scope: CILScope):
        predicate_visit = self.visit(node.predicate, scope)
        body_visit = self.visit(node.body, scope)
        int_key = self.keys_generator.generate('while', True)
        return predicate_visit[0] + body_visit[0], \
               [cil_node.CILWhile(predicate_visit[1],body_visit[1], int_key)]

    @visitor.when(ast.Object)
    def visit(self, node: ast.Object, scope: CILScope):
        real_name = scope.get_real_name(node.name)
        if real_name == '':
            return [], [cil_node.CILGetAttr(self._att_offset(scope.classname, node.name))]
        return [], [cil_node.CILGetLocal(real_name)]

    @visitor.when(ast.IsVoid)
    def visit(self, node: ast.IsVoid, scope):
        exp = self.visit(node.expr, scope)
        key = self.keys_generator.generate("isvoid@isvoid", True)
        return exp[0], exp[1] + [cil_node.CILIsVoid(key)]

    @visitor.when(ast.Case)
    def visit(self, node: ast.Case, scope):
        instance = self.visit(node.expr, scope)
        actions = []
        local = instance[0]
        case_key = self.keys_generator.generate("case", True)
        for i in node.actions:
            t = self.visit(i, scope)
            local += t[0]
            action_key = self.keys_generator.generate("case.action", True)
            action = t[1]
            action[0].set_case_tag(case_key)
            action[0].set_action_tag(action_key)
            actions.append(action)
        return local, [cil_node.CILCase(instance[1], actions, case_key)]

    @visitor.when(ast.Action)
    def visit(self, node: ast.Action, scope):
        new_scope = CILScope(scope.classname, scope)
        new_name = self.name_generator.generate(node.name)
        new_scope.add_var(new_name)
        t = self.visit(node.body, new_scope)
        return [new_name] + t[0], [cil_node.CILAction(new_name, node.action_type, t[1])]

    @visitor.when(ast.Self)
    def visit(self, node: ast.Self, scope: CILScope):
        return [], [cil_node.CILSelf()]