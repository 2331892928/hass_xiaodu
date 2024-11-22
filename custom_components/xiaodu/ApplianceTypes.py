class ApplianceTypes:
    def __init__(self):
        pass

    def LIGHT(self):
        return ['LIGHT']

    def SWITCH(self):
        return ['SOCKET', 'WASHING_MACHINE', 'SWITCH']

    def is_switch(self, applianceTypes):
        A = ApplianceTypes()
        switch = A.SWITCH()
        for i in applianceTypes:
            if i in switch:
                return True
        return False

    def is_light(self, applianceTypes):
        A = ApplianceTypes()
        switch = A.LIGHT()
        for i in applianceTypes:
            if i in switch:
                return True
        return False

