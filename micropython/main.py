try:
    import pico_device

except Exception as e:
    print({"type":"log","status":"error","message":e})
    import machine
    machine.reset()