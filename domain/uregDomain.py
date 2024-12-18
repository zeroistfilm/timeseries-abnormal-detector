from pint import UnitRegistry

class UregDomain:
    def __init__(self):
        self.ureg = UnitRegistry(system='IS')
        self.ureg.formatter.default_format = "P"
        self.Q = self.ureg.Quantity
        self.ureg.formatter.default_format = "P"
        self.ureg.define('CFM = 1 foot ** 3 / minute = cfm')
        self.ureg.define('CMM = 1 meter ** 3 / minute = cmm')
        self.ureg.define('CMH = 1 meter ** 3 / hour = cmh')
        self.ureg.define('m = 1 meter')
        self.ureg.define('ft = 1 foot')
        self.ureg.define('min = 1 minute')
        self.ureg.define('s = 1 second')
        self.Q = self.ureg.Quantity