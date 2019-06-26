# Cool Compiler Project

## Integrantes
- [Joel David Hernández Cruz](https://github.com/JDavid17)
- [Juan José Roque Cires](https://github.com/jr638091)
- [Julio César Sánchez García](https://github.com/julioc1p)

## Content

Development Status.

| Compiler Stage     | Python Module                         | Status                                     |
|:-------------------|:--------------------------------------|:-------------------------------------------|
| Lexical Analysis   | [lexer.py](/src/lexer.py)                            | **complete**                |
| Parsing            | [parser.py](/src/parser.py)                          | **complete**                |
| Semantic Analysis  | [semantic_analizaer.py](/src/semantic_analizaer.py)  | **complete**                |
| Code Generation    | [mips_generator.py](/src/mips_genertor.py);          | **complete**                |


### Lexer & Parser
El proyecto esta desarrollado en python, para el desarrollo del lexer y el parser usamos la herramienta de parsing **ply**, que es una implementacion de **Lex** y **Yac** originales de **C** en python.

#### Grámatica
La Grámatica usada, tiene recursión extrema izquierda, los problemas de ambiguedad se resuelven luego en el parser, definiendo ciertas reglas de presedencia para los tokens. Ejemplo
```python
precedence = (
     ('left', 'PLUS', 'MINUS'),
     ('left', 'TIMES', 'DIVIDE'),
 )
 # Esta declaracion define que PLUS/MINUS tienen el mismo nivel de presedencia y son asociativos a la izquierda, al igual que TIMES/DIVIDE. Dentro de esta declaracion los tokens son ordenados de baja a alta presedencia, luego esta declaracion definiria que TIMES/DIVIDE tienen un mayor nivel de presedencia que PLUS/MINUS
``` 
```Coo
<program> 	 			::= <classes>

<classes> 	 			::= <classes><class>; 
			 			|   <class>;
			 			
<class> 	 			::= class TYPE <inherits> { <features_list_opt> }

<inhertits>  			::= inherits TYPE
			 			|   <empty>

<features_list_opt>     ::= <features_list>
                        |   <empty>

<features_list>         ::= <features_list> <feature> ;
                        |   <feature> ;

<feature>               ::= ID ( <formal_params_list_opt> ) : TYPE { <expression> }
                        |   <formal>
			 			
<formal_params_list_opt>::= <formal_params_list>
                        |   <empty>

<formal_params_list>    ::= <formal_params_list> , <formal_param>
                        |   <formal_param>

<formal_param>          ::= ID : TYPE
			 			
<expr> 		 			::= ID <- <expr>
             			|   <expr>.ID( <arguments_list_opt> )
             			|   <expr>@TYPE.ID( <arguments_list_opt> )
             			|   <if>
             			|   <while>
             			|   <block_expr>
             			|   <let>
             			|   <case>
             			|   new TYPE
             			|   isVoids <expr>
             			|   not <expr>
                        |   <expr> + <expr>
                        |   <expr> - <expr>
                        |   <expr> * <expr>
                        |   <expr> / <expr>
                        |   ~ <expr>
                        |   <expr> < <expr>
                        |   <expr> <= <expr>
                        |   <expr> = <expr>
             			|   <comment>
             			|	( <expr> )
                        |   SELF
             			|   ID
             			|   STRING
             			|   TRUE
             			|   FALSE
                        |	INTEGER

<arguments_list_opt>      ::= <arguments_list>
                          |   <empty>

<arguments_list>        ::= <arguments_list_opt>, <expression>
                        |   <expression>
                        
<case>                  ::= case <expression> of <case_actions> esac

<case_action>           ::= ID : TYPE => <expr>

<case_actions>          ::= <case_action>
                        |   <case_action> <case_actions>
			   			
<let_expression>        ::= let <formal_list> in <expression>

<formal_list>           ::= <formal_list>, <formal>
                        |   <formal>

<formal>                ::= ID : TYPE <- <expression>
                        |   ID : TYPE

<while>		 			::= while <expr> loop <expr> pool

<if>		 			::= if <expr> then <expr> else <expr> fi

<block_expr> 			::= { <block_list> }

<block_list> 			::= <block_list> <expr> ;
             			|   <expr> ;
             			
<empty>      			::=
```

#### Lexer
Para la implementación del lexer, definimos una lista de tokens, que define todos los posibles nombres que pueden tomar los tokens. Esta lista tambien es usada más adelante para identificar los terminales. Cada token esta especificado por una expresion regular compatible con el módulo **re** de Python. Ejemplo:
```python
tokens = (
   'NUMBER',
   'PLUS',
)
# El nombre que le sigue a t_ debe machear exactamente con el del token correspondiente
t_PLUS = 'r\+'

def t_NUMBER(t):
         r'\d+'
         t.value = int(t.value)    
         return t
```

#### Parser
Para la implementación del parser, hacemos uso de **ast.py**. Cada regla de la grámatica la definimos en Python, donde el docstring de la función contiene la especificación de la grámatica libre de contexto correspondiente. Ejemplo:
```python
# Ejemplo de uso
def p_class(self, parse):
        """
        class : CLASS TYPE LBRACE features_list_opt RBRACE
        """
        parse[0] = AST.Class(name=parse[2], parent="Object", features=parse[4])
```

### Ánalisis Semántico
Todo..

### Generación de Código

#### Cool -> Cil
Todo...

#### Cil -> 
Todo...

## Compilando su proyecto

Si es necesario compilar su proyecto, incluya todas las instrucciones necesarias en el archivo [`/src/makefile`](/src/makefile) que está en esta misma carpeta.
Durante la evaluación su proyecto se compilará ejecutando la siguiente secuencia:

```bash
$ cd source
$ make clean
$ make
```

## Ejecutando su proyecto

Incluya en el archivo [`/src/coolc.sh`](/src/compile.sh) todas las instrucciones que hacen falta para lanzar su compilador. Recibirá como entrada un archivo con extensión `.cl` y debe generar como salida un archivo `.mips` cuyo nombre será el mismo que la entrada.

Para lanzar el compilador, se ejecutará la siguiente instrucción:

```bash
$ cd source
$ ./compile.sh <input_file.cl>
```

> **NOTA:** Su proyecto será ejecutado y evaluado en un entorno **Linux**. Si usted desarrolló en un entorno diferente, asegúrese de que es posible ejecutar su proyecto en Linux. En el caso de **.NET**, vea las instrucciones para portar su proyecto a **.NET Core** (la versión Open Source) [aquí](https://.net.microsoft.com/) y asegúrese de probar que funciona en Linux. **NO es posible** entregar su proyecto en forma de una solución que necesite abrirse con Visual Studio para funcionar.

## Sobre el funcionamiento del compilador

El compilador de COOL se ejecutará como se ha definido anteriormente.
En caso de que no ocurran errores durante la operación del compilador, **coolc.sh** deberá terminar con código de salida 0, generar (o sobrescribir si ya existe) en la misma carpeta del archivo **.cl** procesado, y con el mismo nombre que éste, un archivo con extension **.mips** que pueda ser ejecutado con **spim**. Además, reportar a la salida estándar solamente lo siguiente:

    <línea_con_nombre_y_versión_del_compilador>
    <línea_con_copyright_para_el_compilador>

En caso de que ocurran errores durante la operación del compilador, **coolc.sh** deberá terminar con código
de salida (exit code) 1 y reportar a la salida estándar (standard output stream) lo que sigue...

    <línea_con_nombre_y_versión_del_compilador>
    <línea_con_copyright_para_el_compilador>
    <línea_de_error>_1
    ...
    <línea_de_error>_n

... donde `<línea_de_error>_i` tiene el siguiente formato:

    (<línea>,<columna>) - <tipo_de_error>: <texto_del_error>

Los campos `<línea>` y `<columna>` indican la ubicación del error en el fichero **.cl** procesado. En caso
de que la naturaleza del error sea tal que no pueda asociárselo a una línea y columna en el archivo de
código fuente, el valor de dichos campos debe ser 0.

El campo `<tipo_de_error>` será alguno entre:

- `CompilerError`: se reporta al detectar alguna anomalía con la entrada del compilador. Por ejemplo, si el fichero a compilar no existe.
- `LexicographicError`: errores detectados por el lexer.
- `SyntacticError`: errores detectados por el parser.
- `NameError`: se reporta al referenciar un `identificador` en un ámbito en el que no es visible.
- `TypeError`: se reporta al detectar un problema de tipos. Incluye:
    - incompatibilidad de tipos entre `rvalue` y `lvalue`,
    - operación no definida entre objetos de ciertos tipos, y
    - tipo referenciado pero no definido.
- `AttributeError`: se reporta cuando un atributo o método se referencia pero no está definido.
- `SemanticError`: cualquier otro error semántico.

## Sobre la Implementación del Compilador de COOL

Para la implementación del compilador Ud. debe utilizar una herramienta generadora de analizadores
lexicográficos y sintácticos. Puede utilizar la que sea de su preferencia.