# Prueba del analizador RISC-V

.data
numero: .word 10, 20, 30
mensaje: .string "Hola # RISC-V"

.text
main:
    addi t0, zero, 10
    addi t1, zero, 20
    add t2, t0, t1

loop: beq t2, zero, fin
      lw a0, 8(sp)
      sw a0, (sp)
      j loop

fin: nop