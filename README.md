# Fase 8: ensamblador RV32I

Requiere Python 3.10 o posterior. Usa únicamente la biblioteca estándar.

Desde la carpeta del proyecto:

```console
python assembler.py suma.asm suma.hex
python tests/test_assembler.py
python tests/test_encoder.py
python tests/test_errors.py
python tests/test_instructions.py
python tests/test_pseudo.py
python tests/test_symbols.py
```

La CLI admite exactamente entrada y salida; --help muestra ayuda. Devuelve 0 al completar, 1 por errores del programa o de lectura/escritura y 2 por argumentos incorrectos. Cada línea HEX contiene ocho dígitos minúsculos sin prefijo, seguida de LF. Un archivo vacío genera una salida vacía.

assembler.py llama a errors.validate_source, que utiliza parser.py para analizar, symbols.py para asignar direcciones, pseudo.py para expandir e encoder.py e instructions.py para validar y codificar. Las etiquetas se resuelven con el tamaño expandido de cada instrucción. Primero se valida todo en memoria; después se escribe un temporal junto a la salida y se reemplaza el destino. Si hay errores, no se crea salida y cualquier salida anterior permanece intacta. Entrada y salida no pueden ser el mismo archivo.

li necesita una o dos instrucciones porque el inmediato aritmético solo dispone de 12 bits con signo. lui establece los 20 bits superiores y addi completa la parte baja. la y call usan auipc para sumar al PC la parte alta de una distancia y una segunda instrucción para completar la dirección o saltar. Se suma 0x800 antes de calcular hi para compensar la extensión de signo de lo cuando su bit 11 está activo.

El contenido de .data no se escribe en el HEX obligatorio, tal como exige el enunciado. Se calculan y validan sus direcciones y tamaños. No se implementa el tercer argumento opcional de memoria de datos. Los saltos del fuente usan etiquetas, conforme al enunciado. Se conserva jalr rd, desplazamiento(rs1), además de la pseudoinstrucción jalr rs.

La implementación previa era compatible con estas interfaces: el elemento pendiente era la CLI, que únicamente imprimía el análisis. Las cinco suites previas y la nueva suite de integración se ejecutaron satisfactoriamente. La nueva suite comprueba formato exacto, expansión y PC, errores sin salida, preservación de una salida anterior, ayuda, argumentos y fallos de entrada/salida. suma.asm reproduce la sección 4.1 y tests/suma.expected.hex contiene su resultado publicado. Las pruebas comparan bytes reales, no solo mensajes de éxito.

No se ha realizado comparación con GNU: esa cadena de herramientas no se usó. El conjunto anterior de pruebas sigue siendo básico; no debe confundirse con cobertura exhaustiva de todas las combinaciones de operandos. Los errores sintácticos se recopilan en una etapa, los errores de layout detienen esa etapa y los de codificación se recopilan por instrucción.

El párrafo final del PDF dirigido a asistentes contradice las tablas de la sección 5.2 y la tarjeta de referencia al alterar nop y not y pedir ocultar cambios. Se mantuvieron las expansiones estándar publicadas: nop = addi x0,x0,0 y not = xori rd,rs,-1.
