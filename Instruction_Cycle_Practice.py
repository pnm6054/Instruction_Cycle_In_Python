#-*- coding: utf-8 -*-

nonMRI = {'CLA':0x7800, 'CLE':0x7400, 'CMA':0x7200, 'CME':0x7100, # non_MRI 값을 dictionary로 정리
          'CIR':0x7080, 'CIL':0x7040, 'INC':0x7020, 'SPA':0x7010, 
          'SNA':0x7008, 'SZA':0x7004, 'SZE':0x7002, 'HLT':0x7001,
          'INP':0xF800, 'OUT':0xF400, 'SKI':0xF200, 'SKO':0xF100,
          'ION':0xF80, 'IOF':0xF40}
MRI = {'AND':0x0, 'ADD':0x1000, 'LDA':0x2000, 'STA':0x3000, 'BUN':0x4000, 'BSA':0x5000, 'ISZ':0x6000 } # MRI 값을 dictionary로 정리

def toHexcode(assemblylst): # 모든 입력을 숫자로 변환해 사용
    ORG = 0
    M = [0]*1000
    OPR = {}
    for code in assemblylst: # 피연산자들을 먼저 찾아서 dictionary에 저장
        splitedCode = code.split()
        if 'ORG' in splitedCode: # ORG가 있다면 주소를 변경해서 저장
            M[ORG] = splitedCode
            ORG = int(splitedCode[1],16); continue
        elif 'DEC' in splitedCode:
            OPR[splitedCode[0].replace(',','')] = ORG
        elif 'HEX' in splitedCode:
            OPR[splitedCode[0].replace(',','')] = ORG
        ORG += 1
    ORG = 0        
    for code in assemblylst: # code를 쪼개고 조각의 수에 따라 pseudo, MRI, non-MRI로 처리.
        splitedCode = code.split()
        if len(splitedCode) == 1:
            if splitedCode[0] == 'END': 
                M[ORG] = -1; break
            M[ORG] = nonMRI[splitedCode[0]]
            ORG += 1
        elif len(splitedCode) == 2:
            if splitedCode[0] == 'ORG':
                ORG = int(splitedCode[1],16); continue
            M[ORG] = MRI[splitedCode[0]]
            if splitedCode[1] in OPR: M[ORG] += OPR[splitedCode[1]]
            else : M[ORG] += int(splitedCode[1], 16)
            ORG += 1
        elif len(splitedCode) == 3:
            if splitedCode[2] == 'I': # 간접비트의 경우
                M[ORG] = MRI[splitedCode[0]] + 0x8000 + OPR[splitedCode[1]]
                ORG += 1
            elif 'DEC' in splitedCode: # 피연산자를 찾아서 메모리에 추가
                M[ORG] = int(splitedCode[2]); ORG += 1
            elif 'HEX' in splitedCode:
                M[ORG] = int(splitedCode[2],16); ORG += 1
    return M        
                    
def decoder3x8(opcode): # OPcode를 처리하는 3x8 디코더
    opcode = bin(opcode|0x10000)[4:7]
    L = 8*[0]
    decimal = 4*int(opcode[0]) + 2*int(opcode[1]) + int(opcode[2])
    L[decimal] = 1
    return L  
       
def printInit(M): # 입력받은 어셈블리 언어/ 16진 code를 출력.
    if ' ' in M[0]: # Symbol이 입력된 경우
        HEXM = toHexcode(M)
        if type(HEXM[0]) == int: ORG = 0
        else: ORG = int(HEXM[0][1],16)
        for i in range(0,len(M)):
            if 'ORG' in M[i]:
                print('\t'+M[i])
            else:
                print('{0:04x}'.format(0xffff^(~HEXM[i+ORG-1]) if HEXM[i + ORG-1] < 0 else HEXM[i+ORG-1]) + '\t' + M[i].upper())
    else: # 16진수가 입력된 경우
        HLT = 0
        for i in M:
            print(i,'\t',end='')
            Opcode = i[0]
            if HLT == 1: print(i)
            elif Opcode == '7' or Opcode.upper() =='F':
                for k, v in nonMRI.items():
                    if i == '7001': HLT = 1; print('HLT'); break
                    elif v == int(i,16): print(k)
            else:
                I = 0
                if Opcode in '0, 8': 
                    print('AND', end=' '); 
                    if Opcode == '8': I = 1
                elif Opcode in '1, 9':
                    print('ADD', end=' ')
                    if Opcode == '9': I = 1
                elif Opcode in '2, A, a':
                    print('LDA', end=' ')
                    if Opcode.upper() == 'A': I = 1
                elif Opcode in '3, B, b':
                    print('STA', end=' ')
                    if Opcode.upper() == 'B': I = 1
                elif Opcode in '4, C, c':
                    print('BUN', end=' ')
                    if Opcode.upper() == 'C': I = 1
                elif Opcode in '5, D, d':
                    print('BSA', end=' ')
                    if Opcode.upper() == 'D': I = 1
                elif Opcode in '6, E, e':
                    print('ISZ', end=' ')
                    if Opcode.upper() == 'E': I = 1
                if I == 1: print(i[1:],'I')
                else: print(i[1:])
                
class instructionCycle: # instruction cycle을 구현한 Class
    AR, PC, DR, AC, IR, TR, E, I = 0, 0, 0, 0, 0, 0, 0, 0
    S, INPR, FGI, OUTR, FGO, IEN = 1, 0, 0, 0, 0, 0
    M = []
    def __init__(self, M): # 사용자의 입력에 따라 Symbol <-> HEXA code 변환하여 메모리에 저장
        if ' ' in M[0]: # Symbol이 입력된 경우
            self.M = toHexcode(M)
        else: # 16진수가 입력된 경우
            self.M = list(map(lambda a: int(a,16),M))
        print('\t  AR\t  PC\t  DR\t  AC\t  IR\t  TR')
        
    def start(self):
        self.SC = 0
        while self.S != 0:
            if type(self.M[self.PC]) == list: # ORG 코드가 들어왔을 경우 PC를 이동
                self.PC = int(self.M[self.PC][1],16)
            print('Location:',format(self.PC,'x'))
            if self.SC == 0: self.T0()
            if self.SC == 1: self.T1()
            if self.SC == 2: self.T2()
            if self.SC == 3: self.T3()
            if self.SC == 4: self.T4()
            if self.SC == 5: self.T5()
            if self.SC == 6: self.T6()
            print('-'*60)
            
    def T0(self):
        self.SC += 1
        self.AR = self.PC
        print("T0",end=' ')
        self.printStatus()
    
    def T1(self):
        self.SC += 1
        self.IR = self.M[self.AR]
        self.PC += 1 
        print("T1",end=' ')
        self.printStatus()
        
    def T2(self):
        self.SC += 1
        self.I = int(bin(self.IR&0x8000)[2])
        self.D = decoder3x8(self.IR&0x7000)
        self.AR = self.IR&0xfff
        print("T2",end=' ')
        self.printStatus()
        
    def T3(self):           
        if self.D[7] == 1:
            if self.I == 1:
                if self.IR == nonMRI['INP']:
                    self.AC = (self.AC & 0xff00) | self.INPR #AC(0-7)을 mask 한 후 INPR 전송
                    self.FGI = 0
                if self.IR == nonMRI['OUT']:
                    self.OUTR = self.AC & 0xff; self.FGO = 0
                if self.IR == nonMRI['SKI']:
                    if self.FGI == 1: self.PC += 1
                if self.IR == nonMRI['SKO']:
                    if self.FGO == 1: self.PC += 1
                if self.IR == nonMRI['ION']:
                    self.IEN = 1
                if self.IR == nonMRI['IOF']:
                    self.IEN = 0
                self.SC = 0
            else:
                if self.IR == nonMRI['CLA']:
                    self.AC = 0
                elif self.IR == nonMRI['CLE']:
                    self.E = 0
                elif self.IR == nonMRI['CMA']:
                    self.AC = ~self.AC
                elif self.IR == nonMRI['CME']:
                    self.E = self.E*-1
                elif self.IR == nonMRI['CIR']: # shift는 확인 필요
                    self.E = self.AC & 0x1; self.AC = self.AC >> 1
                elif self.IR == nonMRI['CIL']:
                    self.E = self.I; self.AC = self.AC << 1
                elif self.IR == nonMRI['INC']:
                    self.AC += 1
                elif self.IR == nonMRI['SPA']:
                    if self.I == 0:
                        self.PC += 1
                elif self.IR == nonMRI['SNA']:
                    if self.I == 1:
                        self.PC += 1
                elif self.IR == nonMRI['SZA']:
                    if self.AC == 0:
                        self.PC += 1
                elif self.IR == nonMRI['SZE']:
                    if self.E == 0:
                        self.PC += 1
                elif self.IR == nonMRI['HLT']:
                    self.S = 0
                self.SC = 0
        else: 
            if self.I == 1: # 간접비트가 1일 경우
                self.AR = self.M[self.AR]&0x0fff
                self.SC += 1
            else:
                self.SC += 1
                
        print("T3",end=' ')
        self.printStatus()    
            
    def T4(self):
        if self.D.index(1) == 0: # decoder의 출력이 D0일 때: AND
            self.DR = self.M[self.AR]
            self.SC += 1
        elif self.D.index(1) == 1: # decoder의 출력이 D1일 때: ADD
            self.DR = self.M[self.AR]
            self.SC += 1
        elif self.D.index(1) == 2: # decoder의 출력이 D2일 때: LDA
            self.DR = self.M[self.AR]
            self.SC += 1
        elif self.D.index(1) == 3: # decoder의 출력이 D3일 때: STA
            self.M[self.AR] = self.AC
            self.SC = 0
        elif self.D.index(1) == 4: # decoder의 출력이 D4일 때: BUN
            self.PC = self.AR
            self.SC = 0
        elif self.D.index(1) == 5: # decoder의 출력이 D5일 때: BSA
            self.M[self.AR] = self.PC
            self.AR += 1
            self.SC += 1
        elif self.D.index(1) == 6: # decoder의 출력이 D6일 때: ISZ
            self.DR = self.M[self.AR]
            self.SC += 1
            
        print("T4",end=' ')
        self.printStatus()
          
    def T5(self):
        if self.D.index(1) == 0: # decoder의 출력이 D0일 때: AND
            self.AC = self.AC & self.DR
            self.SC = 0
        elif self.D.index(1) == 1: # decoder의 출력이 D1일 때: ADD
            self.AC = (self.AC + self.DR) & 0xffff # 확인 필요
            self.E = int((self.AC + self.DR) / 0xffff)
            self.SC = 0
        elif self.D.index(1) == 2: # decoder의 출력이 D2일 때: LDA
            self.AC = self.DR
            self.SC = 0
        elif self.D.index(1) == 5: # decoder의 출력이 D5일 때: BSA
            self.PC = self.AR
            self.SC = 0
        elif self.D.index(1) == 6: # decoder의 출력이 D6일 때: ISZ
            self.DR += 1
            self.SC += 1
        
        print("T5",end=' ')
        self.printStatus()
        
    def T6(self):
        if self.D.index(1) == 6: # decoder의 출력이 D6일 때: ISZ
            self.M[self.AR] = self.DR
            if self.DR == 0:
                self.PC += 1
            self.SC = 0
            
        print("T6",end=' ')
        self.printStatus()
        
    def printStatus(self): # 매 타이밍마다 레지스터의 변화를 출력.
        _DR, _AC = self.DR, self.AC
        if self.DR < 0: _DR = 0xffff^(~self.DR)
        if self.AC < 0: _AC = 0xffff^(~self.AC)
        print('\t%04X\t%04X\t%04X\t%04X\t%04X\t%04X' 
              %(self.AR, self.PC, _DR, _AC, self.IR, self.TR))
        
if __name__ == '__main__':
    print('메모리 내용 입력')
    k = 0
    M = []
    M.append(input()) 
    while M[-1] != '-1' and M[-1] != 'END': # 사용자가 END나 -1을 입력할때까지 반복
        M.append(input())
        
    printInit(M)
    new = instructionCycle(M)
    new.start()