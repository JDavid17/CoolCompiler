# Semantic Analizer

# Authors:  Joel David Hernandez Cruz
#           Juan Jose Roque Cires
#           Julio Cesar Rodriguez Sanchez

# ------------------------------------------------------------------------------------------------------
#   Reference ply (Python Lex-Yacc) Documentation
#
#   Reference links
#   https://www.dabeaz.com/ply/ply.html#ply_nn13
#   http://www.dalkescientific.com/writings/NBN/parsing_with_ply.html
#   https://www.dabeaz.com/ply/PLYTalk.pdf
#
# ------------------------------------------------------------------------------------------------------

import src.visitor as visitor
import src.cil_nodes as cil_node

# Registers
"""
Registers $v0 and $v1 are used to return values from functions.

Registers $a0 – $a3 are used to pass the first four arguments 
to routines (remaining arguments are passed on the stack).

Registers $t0 – $t9 are caller-saved registers that are used to
hold temporary quantities that need not be preserved across calls

Registers $s0 – $s7 (16–23) are callee-saved registers that hold long-lived
values that should be preserved across calls. They are preserve across calls

Register $gp is a global pointer that points to the middle of a 64K block
of memory in the static data segment. Preserve across calls

Register $fp is the frame pointer. Register $fp is saved by every procedure 
that allocates a new stack frame.Preserve across calls

Register $sp (29) is the stack pointer, which points to the last location on
the stack(Points to Free Memory). Preserve across calls

Register $ra only needs to be saved if the callee itself makes a call.
"""

"""
Code Example for Factorial
main (){
    printf ("The factorial of 10 is %d\n", fact (10));
}
int fact (int n){
    if (n < 1)
        return (1);
    else
        return (n * fact (n - 1));
}

    .text
    .globl main
main:
    subu    $sp, $sp, 32    # Stack frame is 32 bytes long
    sw      $ra, 20($sp)    # Save return address
    sw      $fp, 16($sp)    # Save old frame pointer
    addiu   $fp, $sp, 28    # Set up frame pointer

    li      $a0, 10         # Put argument (10) in $a0
    jal     fact            # Call factorial function

    la      $a0,$LC         # Put format string in $a0
    move    $a1,$v0         # Move fact result to $a1
    jal     printf          # Call the print function
    
    lw      $ra,20($sp)     # Restore return address
    lw      $fp,16($sp)     # Restore frame pointer
    addiu   $sp,$sp,32      # Pop stack frame
    jr      $ra             # Return to caller

    .rdata
$LC:
    .ascii  “The factorial of 10 is %d\n\000”
    
    .text
fact:
    subu    $sp, $sp, 32    # Stack frame is 32 bytes long
    sw      $ra, 20($sp)    # Save return address
    sw      $fp, 16($sp)    # Save frame pointer
    addiu   $fp, $sp, 28    # Set up frame pointer
    sw      $a0, 0($fp)     # Save argument (n)
    
    lw      $v0,0($fp)      # Load n
    bgtz    $v0,$L2         # Branch if n > 0
    li      $v0,1           # Return 1
    jr      $L1             # Jump to code to return

$L2:
    lw      $v1,0($fp)      # Load n
    subu    $v0,$v1,1       # Compute n - 1
    move    $a0,$v0         # Move value to $a0

    jal     fact            # Call factorial function
    
    lw      $v1,0($fp)      # Load n
    mul     $v0,$v0,$v1     # Compute fact(n-1) * n

$L1:                        # Result is in $v0
    lw      $ra, 20($sp)    # Restore $ra
    lw      $fp, 16($sp)    # Restore $fp
    addiu   $sp, $sp, 32    # Pop stack
    jr      $ra             # Return to caller
"""


class MIPS:
    def __init__(self, CILObject):
        self.dotType = CILObject.dtpe
        self.dotCode = CILObject.code
        self.dotData = CILObject.data
        self.CILObject = CILObject
        c = CILObject.constructors['Main']
        t = []
        for i in c:
            t += i.exp_code
            t.append(cil_node.CILInitAttr(CILObject._att_offset('Main', i.offset)))
        self.main = cil_node.CILNew(t, 'Main', CILObject.calc_static('Main'))
        self.vars = []
        self.arguments = []
        self.mips_code = []

    def generate_mips(self):
        """
        Visits nodes in self.dot*
        """
        code = ".text\n" \
               ".globl main\n"

        inherithed = "# Inherithed Method\n" \
                     ".inerithed:\n" \
                     "lw $a0, 4($sp)\n" \
                     "lw $a1, 8($sp)\n" \
                     "lw $a0, ($a0)\n" \
                     "lw $a2, ($a0)\n" \
                     "lw $a3, 4($a0)\n" \
                     "lw $a0, ($a1)\n" \
                     "lw $a1, 4($a1)\n" \
                     "sge $t0, $a2, $a0\n" \
                     "sle $t1, $a1, $a3\n" \
                     "and $a0, $t0, $t1\n" \
                     "sw $a0, ($sp)\n" \
                     "subu $sp, $sp, 4\n" \
                     "\n"
        # $a0 -> eax
        # $a1 -> ebx
        # $a2 -> ecx
        # $a3 -> edx

        pos = 0

        self.mips_code.append(inherithed)
        self.mips_code.append(code)

        self.mips_code.append("# Start self.visit(self.main)\n")
        self.mips_code.append("main:")
        self.visit(self.main)

        self.mips_code.append("# Start self.visit(cil_node.CILDynamicDispatch())\n")
        self.visit(cil_node.CILDynamicDispatch(0, self.CILObject._dispatch('Main', 'main')))

        for in_code in self.dotCode:
            print(in_code)
            self.visit(in_code)

        self.mips_code.append("# Start .data segment (data!)")
        self.mips_code.append(".data")
        for s_data in self.dotData:
            self.mips_code.append("msg{}: .asciiz \"{}\"".format(pos, s_data))
            pos += 1

        for tipe in self.dotType:
            words = f"{tipe.cType}: .word {tipe.t_in}, {tipe.t_out}"
            for method in tipe.methods:
                words += ", " + "." + method

            self.mips_code.append(words)

    @visitor.on('node')
    def visit(self, node):
        pass

    @visitor.when(cil_node.CILArithm)
    def visit(self, node: cil_node.CILArithm):

        self.visit(node.fst[0])
        self.visit(node.snd[0])

        self.mips_code.append("lw $t0, 8($sp)")
        self.mips_code.append("lw $t1, 4($sp)")

        self.mips_code.append("lw $a0, 8($t0)")
        self.mips_code.append("lw $a1, 8($t1)")

        self.mips_code.append("addiu $sp, $sp, 8")

        if node.op == "+":
            self.mips_code.append("add $a1, $a0, $a1")
        elif node.op == "-":
            self.mips_code.append("sub $a1, $a0, $a1")
        elif node.op == "*":
            self.mips_code.append("mult $a0, $a1")
            self.mips_code.append("mflo $a1")
        elif node.op == "/":
            self.mips_code.append("div $a0, $a1")
            self.mips_code.append("mflo $a1")

        # Return value
        self.mips_code.append("li $v0, 9")
        self.mips_code.append("li $a0, 12")
        self.mips_code.append("syscall")

        self.mips_code.append(f"la $t0, Int")
        self.mips_code.append("sw $t0, ($v0)")

        self.mips_code.append("li $t0, 1")
        self.mips_code.append("sw $t0, 4($v0)")

        self.mips_code.append("sw $a1, 8($v0)")
        self.mips_code.append("sw $v0, ($sp)")

        self.mips_code.append("subu $sp, $sp, 4")

    @visitor.when(cil_node.CILBoolOp)
    def visit(self, node: cil_node.CILBoolOp):
        # Move values to $a0-$a1

        self.visit(node.fst[0])
        self.visit(node.snd[0])

        self.mips_code.append("lw $t0, 8($sp)")
        self.mips_code.append("lw $t1, 4($sp)")

        self.mips_code.append("lw $a0, 8($t0)")
        self.mips_code.append("lw $a1, 8($t1)")

        self.mips_code.append("addiu $sp, $sp, 8")

        if node.op == "=":
            self.mips_code.append("seq $a1, $a0, $a1")
        elif node.op == "<":
            self.mips_code.append("slt $a1, $a0, $a1")
        elif node.op == "<=":
            self.mips_code.append("sle $a1, $a0, $a1")

        # Return value
        self.mips_code.append("li $v0, 9")
        self.mips_code.append("li $a0, 12")
        self.mips_code.append("syscall")

        self.mips_code.append(f"la $t0, Bool")
        self.mips_code.append("sw $t0, ($v0)")

        self.mips_code.append("li $t0, 1")
        self.mips_code.append("sw $t0, 4($v0)")

        self.mips_code.append("sw $a1, 8($v0)")
        self.mips_code.append("sw $v0, ($sp)")

        self.mips_code.append("subu $sp, $sp, 4")

    @visitor.when(cil_node.CILNBool)
    def visit(self, node: cil_node.CILNBool):
        self.mips_code.append("lw $a0, {}($sp)".format(4 * node.fst))

        self.mips_code.append("not $a0, $a0")

        # Return value
        self.mips_code.append("sw $a0 $sp")

    @visitor.when(cil_node.CILNArith)
    def visit(self, node: cil_node.CILNArith):
        self.mips_code.append("lw $a0, {}($sp)".format(4 * node.fst))

        self.mips_code.append("li $a1, 1")

        self.mips_code.append("sub $a0, $a1, $a0")

        # Return value
        self.mips_code.append("sw $a0 $sp")

    @visitor.when(cil_node.CILIf)
    def visit(self, node: cil_node.CILIf):
        for i in node.predicate:
            self.visit(i)

        self.mips_code.append("lw $t4, 4($sp)")
        self.mips_code.append("lw $t5, 8($t4)")

        self.mips_code.append("li $t1, 1")
        self.mips_code.append("beq $t5, $t1, {}".format(node.if_tag))
        for i in node.else_body:
            self.visit(i)

        self.mips_code.append("j {}".format(node.end_tag))

        self.mips_code.append("{}:".format(node.if_tag))
        for i in node.then_body:
            self.visit(i)

        self.mips_code.append("{}:".format(node.end_tag))

    @visitor.when(cil_node.CILWhile)
    def visit(self, node: cil_node.CILWhile):
        self.mips_code.append("{}:".format(node.while_tag))
        for i in node.predicate:
            self.visit(i)

        self.mips_code.append("lw $t0, 4($sp)")
        self.mips_code.append("lw $a0, 8($t0)")

        self.mips_code.append("li $t1, 1")
        self.mips_code.append("bne $a0, $t1, {}".format(node.end_tag))
        for i in node.body:
            self.visit(i)

        self.mips_code.append("j {}".format(node.while_tag))
        self.mips_code.append("{}:".format(node.end_tag))

    @visitor.when(cil_node.CILCase)
    def visit(self, node: cil_node.CILCase):
        pass

    @visitor.when(cil_node.CILAction)
    def visit(self, node: cil_node.CILAction):
        self.mips_code.append(f"la $a0, {node.ctype}")
        # self.mips_code.append("lw $t0, 4($sp)")
        self.mips_code.append("sw $a0, ($sp)")
        self.mips_code.append("subu $sp, $sp, 4")

        self.mips_code.append("jal .inerithed")

        self.mips_code.append("lw $a0, 4($sp)")
        self.mips_code.append("addu $sp, $sp, 8")

        self.mips_code.append("li $t0, 0")
        self.mips_code.append("beq $a0, $ti, {}".format(node.if_action_tag))

        self.visit(node.body)

    @visitor.when(cil_node.CILLet)
    def visit(self, node: cil_node.CILLet):
        pass

    @visitor.when(cil_node.CILBlock)
    def visit(self, node: cil_node.CILBlock):
        self.mips_code.append("lw $a0, 4($sp)")
        self.mips_code.append("addu, $sp, $sp, {}".format(4 * node.size))
        self.mips_code.append("sw $a0, ($sp)")
        self.mips_code.append("subu, $sp, $sp, 4")

    @visitor.when(cil_node.CILInitAttr)
    def visit(self, node: cil_node.CILInitAttr):
        self.mips_code.append("# Init Attr")
        self.mips_code.append("lw $t0, 4($sp)")
        self.mips_code.append("lw $t1, 8($sp)")
        self.mips_code.append("addi $t1, $t1, 8")
        self.mips_code.append("sw $t0, {}($t1)".format(node.offset))
        self.mips_code.append("addu $sp, $sp, 4")

    @visitor.when(cil_node.CILNew)
    def visit(self, node: cil_node.CILNew):
        # self.mips_code.append("sw $ra, ($sp)")
        # self.mips_code.append("subu $sp, $sp, 4")
        # self.mips_code.append("sw $fp, ($sp)")
        # self.mips_code.append("subu $sp, $sp, 4")
        # self.mips_code.append("move $fp, $sp")

        self.mips_code.append("li $v0, 9")
        self.mips_code.append("li $a0, {}".format(4 * (node.size + 2)))
        self.mips_code.append("syscall")
        # $v0 contains address of allocated memory
        self.mips_code.append("sw $v0, 0($sp)")
        self.mips_code.append("subu $sp, $sp ,4")

        self.mips_code.append(f"la $t0, {node.ctype}")
        self.mips_code.append("sw $t0, ($v0)")
        # Push node.size
        self.mips_code.append("li $t0, {}".format(node.size))
        self.mips_code.append("sw $t0, 4($v0)")

        for attr in node.attributes:
            print("attr: " + str(attr))
            self.visit(attr)

    @visitor.when(cil_node.CILSelf)
    def visit(self, node: cil_node.CILSelf):
        self.mips_code.append("lw $a0, 12($fp)")
        self.mips_code.append("sw $a0, 0($sp)")
        self.mips_code.append("subu $sp, $sp, 4")

    @visitor.when(cil_node.CILInteger)
    def visit(self, node: cil_node.CILInteger):
        self.mips_code.append("li $v0, 9")
        self.mips_code.append("li $a0, {}".format(12))
        self.mips_code.append("syscall")

        self.mips_code.append(f"la $t0, Int")
        self.mips_code.append("sw $t0, ($v0)")

        self.mips_code.append("li $t0, 1")
        self.mips_code.append("sw $t0, 4($v0)")

        self.mips_code.append("li $a0, {}".format(node.value))
        self.mips_code.append("sw $a0, 8($v0)")
        self.mips_code.append("sw $v0, ($sp)")

        self.mips_code.append("subu $sp, $sp, 4")

    @visitor.when(cil_node.CILBoolean)
    def visit(self, node: cil_node.CILBoolean):
        self.mips_code.append("li $v0, 9")
        self.mips_code.append("li $a0, 12")
        self.mips_code.append("syscall")

        self.mips_code.append(f"la $t0, Bool")
        self.mips_code.append("sw $t0, ($v0)")

        self.mips_code.append("li $t0, 1")
        self.mips_code.append("sw $t0, 4($v0)")

        self.mips_code.append("li $a0, {}".format(node.value))
        self.mips_code.append("sw $a0, 8($v0)")
        self.mips_code.append("sw $v0, ($sp)")

        self.mips_code.append("subu $sp, $sp, 4")

    @visitor.when(cil_node.CILString)
    def visit(self, node: cil_node.CILString):
        self.mips_code.append("li $v0, 9")
        self.mips_code.append("li $a0, 12")
        self.mips_code.append("syscall")

        self.mips_code.append(f"la $t0, String")
        self.mips_code.append("sw $t0, ($v0)")

        self.mips_code.append("li $t0, 1")
        self.mips_code.append("sw $t0, 4($v0)")

        self.mips_code.append("la $a0, msg{}".format(node.pos))
        self.mips_code.append("sw $a0, 8($v0)")
        self.mips_code.append("sw $v0, ($sp)")

        self.mips_code.append("subu $sp, $sp, 4")

    @visitor.when(cil_node.CILDynamicDispatch)
    def visit(self, node: cil_node.CILDynamicDispatch):
        self.mips_code.append("lw $t0, 4($sp)")
        self.mips_code.append("lw $t1, ($t0)")
        self.mips_code.append("lw $t2, {}($t1)".format(4 * (node.method + 2)))

        self.mips_code.append("sw $ra, ($sp)")
        self.mips_code.append("subu $sp, $sp, 4")
        self.mips_code.append("sw $fp, ($sp)")
        self.mips_code.append("subu $sp, $sp, 4")
        self.mips_code.append("move $fp, $sp")

        self.mips_code.append("jal $t2")

        self.mips_code.append("lw $t0, 4($sp)")
        self.mips_code.append("addu $sp, $sp, {}".format(4 * (node.c_args + 2)))
        self.mips_code.append("sw $t0, ($sp)")
        self.mips_code.append("subu $sp, $sp, 4")

    @visitor.when(cil_node.CILStaticDispatch)
    def visit(self, node: cil_node.CILStaticDispatch):
        self.mips_code.append("sw $ra, ($sp)")
        self.mips_code.append("subu $sp, $sp, 4")
        self.mips_code.append("sw $fp, ($sp)")
        self.mips_code.append("subu $sp, $sp, 4")
        self.mips_code.append("move $fp, $sp")

        self.mips_code.append("jal {}".format(node.method))

        self.mips_code.append("lw $t0, 4($sp)")
        self.mips_code.append("addu $sp, $sp, {}".format(4 * (node.c_args + 2)))
        self.mips_code.append("sw $t0, ($sp)")
        self.mips_code.append("subu $sp, $sp, 4")

    @visitor.when(cil_node.CILMethod)
    def visit(self, node: cil_node.CILMethod):
        self.vars = node.local
        self.arguments = node.params

        self.mips_code.append("{}:".format(node.name))
        self.mips_code.append("subu $sp, $sp, {}".format(4 * len(node.local)))

        for code in node.body:
            print(code)
            self.visit(code)

        self.mips_code.append("move $sp, $fp")
        self.mips_code.append("addu $sp, $sp, 4")
        self.mips_code.append("lw $fp, ($sp)")
        self.mips_code.append("addu $sp, $sp, 4")
        self.mips_code.append("lw $ra, ($sp)")

        # self.mips_code.append("lw $fp, 4($sp)")
        # self.mips_code.append("sw $t0, -4($sp)")
        self.mips_code.append("jr $ra")

    @visitor.when(cil_node.CILCopy)
    def visit(self, node: cil_node.CILCopy):
        self.mips_code.append("jal .Object.copy")

    @visitor.when(cil_node.CILGetAttr)
    def visit(self, node: cil_node.CILGetAttr):
        self.mips_code.append("lw $t0, 12($fp)")
        self.mips_code.append("addu $t0, $t0, 8")
        self.mips_code.append(f"addu $t0, $t0, {4*node.offset}")
        self.mips_code.append("lw $t0, ($t0)")
        self.mips_code.append("sw $t0, ($sp)")
        self.mips_code.append("subu $sp, $sp, 4")

    @visitor.when(cil_node.CILGetLocal)
    def visit(self, node: cil_node.CILGetLocal):
        if node.name in self.arguments:
            index = self.arguments.index(node.name)
            self.mips_code.append(f"lw $t0, {12 + 4*index}($fp)")
        elif node.name in self.vars:
            index = self.vars.index(node.name)
            self.mips_code.append(f"lw $t0, -{4*index}($fp)")
        self.mips_code.append("sw $t0, ($sp)")
        self.mips_code.append("subu $sp, $sp, 4")

    @visitor.when(cil_node.CILSetAttr)
    def visit(self, node: cil_node.CILSetAttr):
        self.mips_code.append("lw $t0, 12($fp)")
        self.mips_code.append("addu $t0, $t0, 8")
        self.mips_code.append(f"addu $t0, $t0, {4*node.offset}")

        self.mips_code.append("lw $t1, 4($sp)")
        self.mips_code.append("sw $t1, ($t0)")

    @visitor.when(cil_node.CILAssignment)
    def visit(self, node: cil_node.CILAssignment):
        if node.dest in self.arguments:
            index = self.arguments.index(node.dest)
            self.mips_code.append(f"lw $t0, {12 + 4*index}($fp)")
        elif node.dest in self.vars:
            index = self.vars.index(node.dest)
            self.mips_code.append(f"lw $t0, -{4*index}($fp)")
        self.mips_code.append("lw $t1, 4($sp)")
        self.mips_code.append("sw $t1, ($t0)")

    @visitor.when(cil_node.CILFormal)
    def visit(self, node: cil_node.CILFormal):
        index = self.vars.index(node.dest)
        self.mips_code.append(f"lw $t0, -{4*index}($fp)")
        if not node.load:
            self.mips_code.append("li $t1, 0")
            self.mips_code.append("sw $t1, ($t0)")
        else:
            self.mips_code.append("lw $t1, 4($sp)")
            self.mips_code.append("sw $t1, ($t0)")
            self.mips_code.append("addu $sp, $sp, 4")

    @visitor.when(cil_node.CILIsVoid)
    def visit(self, node: cil_node.CILIsVoid):
        self.mips_code.append("lw $t0, 4($sp)")
        self.mips_code.append(f"beqz $t0, {node.void_tag}")
        self.mips_code.append("li $t1, 1")
        self.mips_code.append(f"j {node.end_tag}")
        self.mips_code.append(f"{node.void_tag}:")
        self.mips_code.append("li $t1, 0")
        self.mips_code.append(f"{node.end_tag}:")
        self.mips_code.append("sw $t1, 4($sp)")