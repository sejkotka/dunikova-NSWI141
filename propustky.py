# import knihoven
from math import acos, sin, sqrt
 
# objemova hmotnost vody [kg/m3]
rho_vody = 1000      
# prumery betonovych trub z katalogu prefa.cz                  
prumery_trub = [300, 400, 500, 600, 800, 1000, 1200, 1400, 1600, 1800, 2000]
# seznam navrzenych propustku - globalni promenna
propustky = []
Q_needed = 0.0

class Trouba:
    def __init__ (self, dn, sklon, drsnost = 0.014):
        self.dn = dn                    # prumer [mm]
        self.r = dn / 1000 / 2          # polomer [m]
        self.sklon = sklon              # sklon [promile]
        self.sklon_i = sklon / 1000     # sklon [m/m]
        self.drsnost = drsnost            # soucinitel drsnosti betonu [-]  typicky 0.012-0.015
        self.data = self.plneni_v_Q()
        self.proudeni = self.typ_proudeni()
        self.v_max = self.maximalni_rychlost()
        self.Q_max = self.maximalni_prutok()
        self.bystr = self.bystrinne()
    
    def __repr__ (self):
        return f"DN {self.dn} (v max = {round(self.v_max, 3)} m/s, Q max = {round(self.Q_max, 3)} m\u00B3/s)"
    
    def plneni_v_Q(self):
        vysledky = {}
        d_m = self.dn / 1000        
        for plneni in range(101):
            # vypocet podle Chezyho rovnice v = C * sqrt(R*S)
            # Q = A * v = A * C * sqrt(R*S)
            if (plneni == 0) or (self.sklon_i < 0):
                rychlost_v = 0
                prutok_Q = 0
            else:
                h = plneni / 100
                psi = 2 * acos(1 - 2 * h)
                prutocna_plocha_A = ((d_m**2) / 8) * (psi - sin(psi))
                smaceny_obvod_P = d_m * psi / 2
                hydraulicky_polomer_R = prutocna_plocha_A / smaceny_obvod_P
                chezyho_koef_C = (1/self.drsnost) * hydraulicky_polomer_R**(1/6)
                rychlost_v = chezyho_koef_C * sqrt(hydraulicky_polomer_R * self.sklon_i)
                prutok_Q = prutocna_plocha_A * rychlost_v
            vysledky[plneni] = (rychlost_v, prutok_Q)
        return vysledky

    # vypocet Freudeho cisla Fr = v / sqrt(g * h)
    def Freudeho_cisla(self):
        dict_Fr = {}
        d_m = self.dn / 1000        
        for plneni in range(101):      
            if plneni == 0:
                Fr = 0
            else:
                h = plneni / 100
                psi = 2 * acos(1 - 2 * h) 
                prutocna_plocha_A = ((d_m**2) / 8) * (psi - sin(psi))               
                sirka_hladiny_B = d_m * sin(psi / 2)
                if sirka_hladiny_B != 0 and prutocna_plocha_A != 0:
                    hydraulicka_hloubka_h = prutocna_plocha_A / sirka_hladiny_B
                    v = self.data[plneni][0]
                    Fr = v / sqrt(9.81 * hydraulicka_hloubka_h)
                else:
                    Fr = None
            if Fr != None:
                if round(Fr, 5) == 1:
                    dict_Fr[plneni] = 1
                elif (Fr < 1) or (Fr > 1):
                    dict_Fr[plneni] = round(Fr, 5)
                else:
                    dict_Fr[plneni] = None
        return dict_Fr 

    # typ proudeni, kdy Fr < 1 pro ricni proudeni, Fr > 1 pro bystrinne proudeni a Fr = 1 pro kriticke proudeni   
    def typ_proudeni(self):
        proudeni = {}
        dict_Fr = self.Freudeho_cisla()
        for plneni in dict_Fr:
            Fr = dict_Fr[plneni]
            if Fr != None:
                if Fr == 1:
                    proudeni[plneni] = "kritické"
                elif Fr > 1:
                    proudeni[plneni] = "bystřinné"   
                else:
                    proudeni[plneni] = "říční"                    
            else:
                proudeni[plneni] = "chyba výpočtu"       
        return proudeni      

    def bystrinne(self):
        seznam_bystrinne = []
        dict_Fr = self.Freudeho_cisla()
        pocatek = None
        konec = None
        plneni = 0
        for plneni in range(101):
            Fr = dict_Fr[plneni]
            if plneni == 0:
                if Fr > 1:
                    pocatek = plneni
                continue
            else:
                Fr_pred = dict_Fr[plneni - 1]
                if Fr > 1 and Fr_pred <= 1:
                    pocatek = plneni
                if Fr_pred > 1 and Fr <= 1:
                    konec = plneni - 1
                    seznam_bystrinne.append((pocatek, konec))
        return seznam_bystrinne                
    
    def maximalni_rychlost(self):
        data = self.data
        v_max = 0
        for plneni in data:
            v_max = max(data[plneni][0], v_max)
        return v_max
    
    def maximalni_prutok(self):
        data = self.data
        Q_max = 0
        for plneni in data:
            Q_max = max(data[plneni][1], Q_max)
        return Q_max

#-------------------------------------------------------------------------------

from tkinter import *
from tkinter import ttk
from tkinter import font
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt

def navrhni_troubu(Q, sklon_promile):
    if Q == None or sklon_promile == None:
        return None
    else:
        navrhy = []
        for dn in prumery_trub:
            propustek = Trouba(dn, sklon_promile)
            if propustek.maximalni_prutok() >= Q:
                navrhy.append(propustek)
    return navrhy

def vypocitej(Q, sklon_promile):
    global propustky, Q_needed
    label_vysledek.config(text="", foreground="black")
    propustky = navrhni_troubu(Q, sklon_promile)
    Q_needed = Q
    if (propustky == None) or (propustky == []):
        label_vysledek.config(text="Nelze navrhnout propustek.", foreground="red")  
        dn_combobox.config(values=[])
        dn_combobox.set("")        
        vykresli_nahled(frame_graf, None) 
        aktualizuj_tabulku(tree, None)
        # vykresli_tabulku(tree, None)        
    else:  
        nazvy = []
        for propustek in propustky:
            nazvy.append(f"DN {propustek.dn}")                
        dn_combobox.config(values=nazvy)
        dn_combobox.set(nazvy[0])
        # zobrazeni dat pro nejmensi mozny propustek
        vykresli_nahled(frame_graf, propustky[0]) 
        aktualizuj_tabulku(tree, propustky[0])        

def vytvor_graf(propustek):
    global Q_needed
    kategorie = list(propustek.data.keys())
    dolni_hodnoty = [values[0] for values in propustek.data.values()]
    horni_hodnoty = [values[1] for values in propustek.data.values()]
    pozadovana_hodnota = [Q_needed for _ in kategorie]
    y_positions = range(len(kategorie))

    # horni hodnoty (modra cara)
    plt.plot(horni_hodnoty, y_positions, '-', label="Průtok [m\u00B3/s]", color="blue")
    plt.plot(pozadovana_hodnota, y_positions, '--', label="Požadovaný průtok [m\u00B3/s]", color="blue")

    # dolni hodnoty (cervena cara)
    plt.plot(dolni_hodnoty, y_positions, '-', label="Rychlost [m/s]", color="red")

    # Nastavení popisků na svislé ose
    plt.yticks(range(0, 101, 10), range(kategorie[0], kategorie[-1] + 1, 10)) 
     # Název grafu
    plt.suptitle(f"Návrh propustku na požadovaný průtok: Q = {Q_needed} [m\u00B3/s], sklon {str(propustek.sklon)} ‰", fontsize=14) 
    plt.title(f"{str(propustek)}", fontsize=14) 
    plt.xlabel("Průtok a rychlost")
    # plt.xlabel("Průtok a rychlost")
    plt.ylabel("Procento plnění")        
    plt.grid(axis='both', linestyle='--', alpha=0.7)  
    plt.grid(which='minor', axis='x', linestyle=':', alpha=0.7)
    plt.minorticks_on()
    plt.xlim(left=0)
    plt.ylim(bottom=0)
    x_max = 1.1 * max(propustek.v_max, propustek.Q_max)
    plt.xlim(right=x_max)

    # Vyplnění intervalu, kde je bystřinné proudění
    xlim_max = plt.xlim()[1]
    if propustek.bystr:
        interval = propustek.bystr[0]
        if interval[0] != 0:
            plt.text(xlim_max, interval[0]/2, "říční ", fontsize=12, color="orange", ha="right")
        for interval in propustek.bystr:        
            plt.fill_between(plt.xlim(), interval[0], interval[1], color="orange", alpha=0.15, label="bystřinné")
            plt.text(xlim_max, (interval[0] + interval[1])/2, "bystřinné ", fontsize=12, color="orange", ha="right")
        interval = propustek.bystr[-1]
        if interval[1] != 100:
            plt.text(xlim_max, (interval[1] + 100)/2, "říční ", fontsize=12, color="orange", ha="right")
    else:
        dolni, horni = plt.ylim()
        plt.text(xlim_max, (dolni + horni)/2, "říční ", fontsize=12, color="orange", ha="right")       

    # Vykreslení hodnot, kde je kritické proudění
    for plneni in range(101):
        plneni_krit = [plneni for _ in plt.xlim()]
        if propustek.proudeni[plneni] == "kritické":         
            plt.plot(plt.xlim(), plneni_krit, '--', color="orangered") 
            if plneni == 100:
                plt.text(xlim_max, plneni + 1, "kritické ", fontsize=12, color="orangered", ha="right")
            else:
                if propustek.proudeni[plneni + 1] != "kritické":           
                    plt.text(xlim_max, plneni + 1, "kritické ", fontsize=12, color="orangered", ha="right")
    
    plt.legend()  # Zobrazení legendy
    

def prazdny_graf():
    # Prázdný graf při spuštění
    plt.yticks(range(0, 101, 10), range(0, 101, 10))
    plt.title("Graf závislosti průtoku, rychlosti a plnění\n\n")
    plt.suptitle(f"Návrh propustku na požadovaný průtok: Q = ... [m\u00B3/s], sklon ... ‰", fontsize=14) 
    plt.title(f"", fontsize=14) 
    plt.xlabel("Průtok a rychlost")
    plt.ylabel("Procento plnění")
    plt.grid(axis='both', linestyle='--', alpha=0.7)
    plt.grid(which='minor', axis='x', linestyle=':', alpha=0.7)
    plt.minorticks_on()    

def vykresli_nahled(frame, propustek):
    global Q_needed
    fig = plt.figure(figsize=(8, 6))
    if propustek == None:
        prazdny_graf()
    else:
        vytvor_graf(propustek)

    # Vložení grafu do tkinter pomocí FigureCanvasTkAgg
    canvas = FigureCanvasTkAgg(fig, master=frame)
    canvas_widget = canvas.get_tk_widget()
    canvas_widget.grid(column=0, row=0, sticky=(N, W, E, S))  # Graf přes celou šířku frame
    canvas.draw()

    # Připojení události k pravému tlačítku myši
    if propustek != None:
        canvas_widget.bind("<Button-3>", pravym_tlacitkem)

def zobraz_graf_v_okne(propustek):
    global Q_needed
    plt.close('all')
    plt.figure(figsize=(8, 6))
    vytvor_graf(propustek)
    plt.show()    

def vykresli_tabulku(tree, propustek):
    # tree = ttk.Treeview(frame, columns=('plneni', 'v', 'Q', 'typ_proudeni'), show='headings')
    tree.heading('plneni', text='Plnění')
    tree.heading('v', text='v [m/s]')
    tree.heading('Q', text='Q [m\u00B3/s]')
    tree.heading('typ_proudeni', text='Typ proudění')
    
    tree.column('plneni', width=75, anchor="e")
    tree.column('v', width=75, anchor="e")
    tree.column('Q', width=75, anchor="e")
    tree.column('typ_proudeni', width=125, anchor="center")

    if propustek != None:
        for plneni in range(10, 101, 10):
            tree.insert("", 'end', values=(plneni, round(propustek.data[plneni][0], 3), round(propustek.data[plneni][1], 3), propustek.proudeni[plneni]))  

    tree.pack(fill='both', expand=True)

def aktualizuj_tabulku(tree, propustek):
    # Odstranění starých dat z tabulky
    tree.delete(*tree.get_children())
    
    # Přidání nových dat do tabulky
    if propustek != None:
        for plneni in range(10, 101, 10):
            tree.insert("", 'end', values=(plneni, round(propustek.data[plneni][0], 3), round(propustek.data[plneni][1], 3), propustek.proudeni[plneni]))  

def on_export_btn_click():
    if (dn_combobox.current() >= 0) and (len(propustky) > 0):
        zobraz_graf_v_okne(propustky[dn_combobox.current()])
    else:
        pass

def on_dn_combobox_change(event):
    index = dn_combobox.current()   # index vybrane polozky
    if index >= 0:
        vykresli_nahled(frame_graf, propustky[index])
        aktualizuj_tabulku(tree, propustky[index])        
    else:
        vykresli_nahled(frame_graf, None)
        aktualizuj_tabulku(tree, None)

# Funkce pro zachycení kliknutí pravým tlačítkem na graf
def pravym_tlacitkem(event):
    if dn_combobox.get() == "":
        return
    else:
        index = dn_combobox.current()   # index vybrane polozky
        if index >= 0:
            zobraz_graf_v_okne(propustky[index])

# Funkce pro označení celého textu v Entry widgetu při vstupu
def select_all_delayed(widget):
    # Označí text až po dokončení události kliknutí
    widget.select_range(0, 'end')
    widget.icursor('end')

def on_focus_in(event):
    event.widget.after_idle(select_all_delayed, event.widget)

def on_mouse_click(event):
    if event.widget != event.widget.focus_get():
        event.widget.focus_set()
        # Označení proběhne po události kliknutí
        event.widget.after_idle(select_all_delayed, event.widget)
        return 'break'
    
#-----------------------------------------------------------------------------------
# Funkce pro ukončení aplikace
import sys
def zavri_aplikaci():
    okno.quit()  # zajistí čisté ukončení aplikace
    okno.destroy()

#-----------------------------------------------------------------------------------
# základní smyčka
okno = Tk()
okno.protocol("WM_DELETE_WINDOW", zavri_aplikaci)  # Při zavření okna se ukončí aplikace
okno.title("Hydraulické parametry betonových trub")
#okno.tk.call("tk", "scaling", 1.5)  # Škálování pro 150 %

default_font = font.nametofont("TkDefaultFont")
default_font.configure(size=12)
style = ttk.Style()
style.configure("Treeview.Heading", font=default_font)

mainframe = ttk.Frame(okno, padding="3 3 12 12")
mainframe.grid(column=0, row=0, sticky=(N, W, E, S))
okno.columnconfigure(0, weight=1)
okno.rowconfigure(0, weight=1)

prutok = StringVar(value="0.0")
prutok_entry = ttk.Entry(mainframe, width=7, textvariable=prutok, font=default_font)
prutok_entry.grid(column=2, row=1, sticky=(W, E))
# Označí celý text při vstupu (Tab nebo kliknutí po focusu)
prutok_entry.bind("<FocusIn>", on_focus_in)
prutok_entry.bind("<Button-1>", on_mouse_click)

sklon = StringVar(value="0.0")
sklon_entry = ttk.Entry(mainframe, width=7, textvariable=sklon, font=default_font)
sklon_entry.grid(column=2, row=2, sticky=(W, E))
# Označí celý text při vstupu (Tab nebo kliknutí po focusu)
sklon_entry.bind("<FocusIn>", on_focus_in)
sklon_entry.bind("<Button-1>", on_mouse_click)

ttk.Label(mainframe, text="Požadovaný průtok: ").grid(column=1, row=1, sticky=E)
ttk.Label(mainframe, text="m\u00B3/s").grid(column=3, row=1, sticky=W)
ttk.Label(mainframe, text="Sklon propustku: ").grid(column=1, row=2, sticky=E)
ttk.Label(mainframe, text="‰").grid(column=3, row=2, sticky=W)


# Výstupní label
label_vysledek0 = ttk.Label(mainframe, text="Vyhovující DN: ")
label_vysledek0.grid(column=1, row=4, sticky=(E, N))
label_vysledek = ttk.Label(mainframe, text="")
label_vysledek.grid(column=2, row=6, columnspan=3, sticky=W)

# Frame pro graf
frame_graf = ttk.Frame(mainframe, padding="3 3 12 12")
frame_graf.grid(column=1, row=8, columnspan=5, sticky=(N, W, E, S))

# Frame pro tabulku
frame_tree = ttk.Frame(mainframe, padding="3 3 12 12")
frame_tree.grid(column=5, row=1, rowspan=7, sticky=(N, E))
tree = ttk.Treeview(frame_tree, columns=('plneni', 'v', 'Q', 'typ_proudeni'), show='headings')

# ComboBox s moznymi prumery
vysledne_dn = StringVar()
dn_combobox = ttk.Combobox(mainframe, width=7, textvariable=vysledne_dn, font=default_font)
dn_combobox.grid(column=2, row=4, sticky=(W, E))
dn_combobox.bind('<<ComboboxSelected>>', on_dn_combobox_change)
dn_combobox.configure(state="readonly")

ttk.Button(
    mainframe, 
    text="Spustit", 
    command=lambda: vypocitej(float(prutok_entry.get()), float(sklon_entry.get()))
    ).grid(column=4, row=1, rowspan=4, sticky=(N, W, E, S), pady=12)

ttk.Button(
    mainframe, 
    text="Export grafu",
    command=lambda: on_export_btn_click()
    ).grid(column=4, row=5, rowspan=3, sticky=(N, W, E), pady=12)

for child in mainframe.winfo_children(): 
    child.grid_configure(padx=5, pady=5)

mainframe.rowconfigure(7, weight=1)             # Graf má zabrat zbytek místa

# Inicializace prázdného grafu a tabulky
vykresli_nahled(frame_graf, None)
vykresli_tabulku(tree, None)

prutok_entry.focus()

okno.mainloop()
