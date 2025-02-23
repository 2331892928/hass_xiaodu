class ApplianceTypes:
    def __init__(self):
        pass

    def LIGHT(self):
        return ['LIGHT']

    def SWITCH(self):
        return ['SOCKET', 'WASHING_MACHINE', 'SWITCH', 'HEATER', 'AIR_FRESHER', 'WINDOW_OPENER', 'CLOTHES_RACK']

    def COVER(self):
        return ['CURTAIN']

    def CLIMATE(self):
        return ['AIR_CONDITION']

    def BUTTON(self):
        return ['CLOTHES_RACK']

    def LOCK(self):
        return ['DOOR_LOCK']

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

    def is_cover(self, applianceTypes):
        A = ApplianceTypes()
        switch = A.COVER()
        for i in applianceTypes:
            if i in switch:
                return True
        return False

    def is_climate(self, applianceTypes):
        A = ApplianceTypes()
        switch = A.CLIMATE()
        for i in applianceTypes:
            if i in switch:
                return True
        return False

    def is_button(self, applianceTypes):
        A = ApplianceTypes()
        switch = A.BUTTON()
        for i in applianceTypes:
            if i in switch:
                return True
        return False

    def is_lock(self, applianceTypes):
        A = ApplianceTypes()
        switch = A.LOCK()
        for i in applianceTypes:
            if i in switch:
                return True
        return False

