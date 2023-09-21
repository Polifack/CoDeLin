class D_Label:
    def __init__(self, xi, li, sp):
        self.separator = sp

        self.xi = xi if xi is not None else "_"
        self.li = li if li is not None else "_"

    def separate_bits(self, idx):
        '''
        Separates the bits of the label at the specified index.
        '''
        if idx < 0 or idx >= len(self.xi):
            return self.xi, "_"
        
        return self.xi[:idx], self.xi[idx:]

    def __repr__(self):
        return f'{self.xi}{self.separator}{self.li}'

    @staticmethod
    def from_string(lbl_str, sep):
        xi, li = lbl_str.split(sep)
        return D_Label(xi, li, sep)
    
    @staticmethod
    def empty_label(separator):
        return D_Label("", "", separator)
