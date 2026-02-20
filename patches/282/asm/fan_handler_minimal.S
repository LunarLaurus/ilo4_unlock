# Minimal Fan Handler for iLO4 2.82
# This is a simplified version that provides basic 'fan speed <n>' functionality
# Without the full ~5KB CLI parser

# Based on analysis:
# - IPC call function at: 0x01776004 (from 2.82 analysis)
# - Health module handler at: 0x39e064
# - BEQ patch needed at: 0x39e0c4 (0a 00 00 ea -> 00 00 00 ea)

# The handler will be placed in a code cave or unused section
# For 2.82, we can patch into the existing handler area or find space

# Entry point: fan_speed_simple
# Arguments: Fan speed value in R0 (0-255)
# Returns: 0 on success, error code on failure

    .text
    .align 4
    .global fan_speed_simple

fan_speed_simple:
    # Save registers
    PUSH    {R4-R6, LR}
    
    # Validate input (0-255)
    CMP     R0, #0x100
    BCS     invalid_speed       @ If >= 256, error
    
    # Build IPC request structure on stack
    # Structure:
    #   0x00: switch value (6 for fan)
    #   0x04: command (1 for FAN_SET)
    #   0x08: fan speed value
    #   0x0C: reserved (0)
    
    SUB     SP, SP, #0x20       @ Allocate 32 bytes for IPC struct
    
    MOV     R4, #6              @ Switch value 6 = fan
    STR     R4, [SP, #0x00]     @ Store switch value
    
    MOV     R4, #1              @ Command 1 = FAN_SET
    STR     R4, [SP, #0x04]     @ Store command
    
    STR     R0, [SP, #0x08]     @ Store fan speed from R0
    
    MOV     R4, #0
    STR     R4, [SP, #0x0C]     @ Clear reserved
    
    # Call IPC
    # The IPC function at 0x01776004 takes:
    #   R0 = pointer to request structure
    #   R1 = pointer to response structure (can be same as request)
    
    MOV     R0, SP              @ R0 = &ipc_struct
    MOV     R1, SP              @ R1 = &ipc_struct (reused for response)
    
    # Load IPC function address
    # Note: This needs to be adjusted for the actual runtime address
    # In 2.82, external functions are called via PLT stubs
    LDR     R4, =0x01776004
    BLX     R4                  @ Call IPC function
    
    # Check result
    CMP     R0, #0
    BNE     ipc_error
    
    # Success
    MOV     R0, #0              @ Return 0 (success)
    B       cleanup

invalid_speed:
    MOV     R0, #1              @ Return 1 (invalid argument)
    B       cleanup_nostack

ipc_error:
    MOV     R0, #2              @ Return 2 (IPC error)
    @ Fall through to cleanup

cleanup:
    ADD     SP, SP, #0x20       @ Deallocate IPC struct

cleanup_nostack:
    POP     {R4-R6, PC}         @ Restore and return

    .pool

# Alternative: Even simpler hardcoded version
# This version sets a hardcoded fan speed without arguments

    .global fan_speed_fixed
fan_speed_fixed:
    PUSH    {R4, LR}
    SUB     SP, SP, #0x20
    
    MOV     R4, #6
    STR     R4, [SP, #0x00]     @ Switch = 6 (fan)
    MOV     R4, #1
    STR     R4, [SP, #0x04]     @ Command = 1 (FAN_SET)
    
    # Hardcoded speed - change this value as needed
    MOV     R4, #100            @ 100% fan speed
    STR     R4, [SP, #0x08]
    
    MOV     R4, #0
    STR     R4, [SP, #0x0C]
    
    MOV     R0, SP
    MOV     R1, SP
    LDR     R4, =0x01776004
    BLX     R4
    
    ADD     SP, SP, #0x20
    POP     {R4, PC}

    .pool

# Size estimates:
# fan_speed_simple: ~80 bytes
# fan_speed_fixed: ~50 bytes
# 
# These can be placed in:
# 1. A code cave in the binary
# 2. Overwrite the removed CLI parser area (if safe)
# 3. Extend the .text section
#
# To use:
# 1. Patch BEQ at 0x39e0c4 to enable IPC handler
# 2. Patch command table to point to this handler
# 3. Or call directly from a modified SSH shell
