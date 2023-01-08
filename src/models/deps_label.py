class DependencyLabel:
    def __init__(self, xi, li, sp):
        self.separator = sp

        self.xi = xi    # dependency relation
        self.li = li    # encoding

    def __repr__(self):
        return f'{self.xi}{self.separator}{self.li}'

    @staticmethod
    def from_string(lbl_str, sep):
        xi, li = lbl_str.split(sep)
        return DependencyLabel(xi, li, sep)
