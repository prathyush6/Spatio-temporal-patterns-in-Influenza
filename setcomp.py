#!/usr/bin/python
#set compression

##Inputs: D, S
####potentially other inputs: allowed errors
##D has rows r1,...rm and columns c1...cn
##Goal: find a succinct description for the set of rows corresponding to S

##Data structures
## F_r={}: set of features corresponding to rows
#### F_r[i] = "r_"+str(i)
## F_c={}: dictionary which gives the features corresponding to sets of columns
#### k: parameter which determines how many columns we consider in a tuple
#### F_c[t] = [j1, j2, jk_prime]: set of columns j1, j2, ... which correspond to tth feature
###### k_prime <= k
## cov={}: specifies coverage
#### cov[t] = set of rows covered by the set F_c[t]
###### if D[i, j]=1 for all j in F_c[t], we have i in cov[t]
##Variables
## x_r[i]=1 if F_r[i] is considered with a positive coefficient
## y_r[i]=1 if F_r[i] is considered with a negative coefficient
## x_c[i]=1 if F_c[i] is considered with a positive coefficient
## y_c[i]=1 if F_c[i] is considered with a negative coefficient

import time
import sys
import csv
from gurobipy import *
import random

def create_subsets_of_rows(nrow):
  F_r = {}
  for i in range(nrow):
    F_r[i]=i
  return F_r

def create_subsets_of_rows_given_subset(set_rows):
  F_r = {}
  for i in set_rows:
    F_r[i]=i
  return F_r

def create_subsets_of_cols(set_cols, k):
  F_c={}
  num_sets=0
  for i in set_cols:
    #F_c[i] = {i:1}
    F_c[num_sets] = {i:1}
    num_sets +=1
  #print("aaa ", F_c)
  #num_sets=len(set_cols)
  #print("initial num_sets=",num_sets)
  for k_prime in range(1,k):
    #for each set c in F_c, add another element that is not in it
    sets_so_far = list(F_c.keys())
    #print(k_prime, sets_so_far)
    for c in sets_so_far:
      #print("c=", c)
      A={}
      for r in F_c[c].keys(): A[r]=1
      #print("bbb ", A)
      #print("num_sets=", num_sets, F_c)
      #A=F_c[c].keys()
      if (len(A) < k_prime): continue
      for i in set_cols:
        B=A.copy()
        B[i]=1
        flag=1
        for j in F_c:
          if (F_c[j] == B): flag=0
        #print("B=", B, "F_c=", F_c, "flag=", flag)
        #if (i not in A):
        if (flag):
          F_c[num_sets] = F_c[c].copy()
          F_c[num_sets][i]=1
          num_sets+= 1
  return F_c

#example of groups_of_cols
#groups_of_cols[0]={1:1}
#groups_of_cols[1]={15:1, 16:1, 17:1, 18:1} #was1
#groups_of_cols[2]={19:1, 20:1, 21:1, 22:1} #was2
#groups_of_cols[3]={23:1, 24:1, 25:1, 26:1} #was3
#groups_of_cols[4]={27:1, 28:1, 29:1, 30:1} #was4
#return all subsets in which exactly one elt is picked from groups_of_cols[0],
#groups_of_cols[1], etc.
def create_subsets_of_cols_in_groups(groups_of_cols):
  k=len(groups_of_cols)
  A={}
  for i in range(k): A[i]=1
  sets_of_groups=create_subsets_of_cols(A, k)
  G={}
  n_subsets=0
  for s in sets_of_groups:
    B={}; B[0]={}
    for i in groups_of_cols:
      if (i in sets_of_groups[s]):
        C={}; n_subsets_c=0; C[0]={}
        for b in B:
          for j in groups_of_cols[i]:
            C[n_subsets_c] = B[b].copy()
            C[n_subsets_c][j]=1
            n_subsets_c += 1
        B=C.copy()
    for set_b in B:
      G[n_subsets] = B[set_b].copy()
      n_subsets += 1
  return G


#Z: dictionary with variables
#return str
def var_str(Z):
  x=""
  for i in Z:
    x = x+'_'+str(i)
  return x

# def var_str_with_col_names(Z, col_names):
#   x=""
#   for i in Z:
#     x = x+'_'+col_names[i]
#   return x
def var_str_with_col_names(Z, col_names):
  return ",".join(col_names[i] for i in Z)

def coverage(D, F_c):
  inv_cov={}
  nrow=len(D);
  for i in range(nrow):
    inv_cov[i]={}
  for c in F_c:
    col_set = F_c[c]
    A=[]
    #find all rows i st D[i][j]=1 for j in cols corresponding to c
    for i in range(nrow):
      flag=1
      for col in col_set:
        if (D[i][col] ==0): flag=0
      if (flag): A.append(i)
    for i in A:
      inv_cov[i][c]=1
  return inv_cov

def coverage_w_set_rows(D, F_c, set_rows):
  inv_cov={}
  for i in set_rows: inv_cov[i]={}
  for c in F_c:
    col_set = F_c[c]
    A=[]
    #find all rows i st D[i][j]=1 for j in cols corresponding to c
    for i in set_rows:
      flag=1
      for col in col_set:
        if (D[i][col] ==0): flag=0
      if (flag): A.append(i)
    for i in A:
      inv_cov[i][c]=1
  return inv_cov

def print_col_entries(j, D, row_names, set_rows, col_names):
  print (col_names[j], ":", end=" ")
  for i in set_rows:
    if (D[i][j]): print(row_names[i], end=" ")
  print("\n")

def print_set_of_col_entries(col_set, D, row_names, set_rows, col_names):
  rows_corresponding_to_c=[]
  for i in set_rows:
    flag=1
    for j in col_set:
      if (D[i][j]==0): flag=0
    if flag: rows_corresponding_to_c.append(row_names[i])
  print("var=", var_str_with_col_names(col_set, col_names), ":")
  for k in rows_corresponding_to_c: print(k, end=" ")
  print("\n")

#m: gurobi model
#D is a 2d dictionary
#S is dictionary
def setcompress(D, col_names, row_names, S, k, m, relax_par):
  x_r={}; y_r={}; x_c={}; y_c={}; relax={}; col_name_mapx={}; col_name_mapy={};
  row_name_mapx={}; row_name_mapy={}
  nrow=len(D); set_cols=D[0].keys()
  #print col_names
  #print set_cols
  F_r = create_subsets_of_rows(nrow)
  F_c = create_subsets_of_cols(set_cols, k)
  inv_cov = coverage(D, F_c)
  #create variables
  for c in F_r:
    z = str(c)
    x_r[c] = m.addVar(obj = 1, vtype=GRB.BINARY, name = 'x_r_%s' %(z))
    row_name_mapx['x_r_'+z] = row_names[F_r[c]]
    y_r[c] = m.addVar(obj = 1, vtype=GRB.BINARY, name = 'y_r_%s' %(z))
    row_name_mapy['y_r_'+z] = row_names[F_r[c]]
  for c in F_c:
    z = var_str(F_c[c])
    #print F_c[c]
    z1 = var_str_with_col_names(F_c[c], col_names)
    #print "c=", F_c[c]
    #print "z=", z
    x_c[c] = m.addVar(obj = 1, vtype=GRB.BINARY, name = 'x_c%s' %(z))
    y_c[c] = m.addVar(obj = 1, vtype=GRB.BINARY, name = 'y_c%s' %(z))
    #col_name_mapx[x_c[c]] = z1
    col_name_mapx['x_c'+z] = z1
    #col_name_mapy[y_c[c]] = z1
    col_name_mapy['y_c'+z] = z1
  #add variables for relaxing constraints
  for i in range(nrow):
    relax[i] = m.addVar(vtype=GRB.BINARY, name = 'relax_%s' %(i))
  #create constraints
  #print "S={}".format(S)
  for i in range(nrow):
    if (S[i]):
      #m.addConstr(quicksum(x_r[c] for c in F_r) + quicksum(x_c[c] for c in inv_cov[i]) - quicksum(y_r[c] for c in F_r) - quicksum(y_c[c] for c in inv_cov[i]) >= 1, 'const_%s' %(i))
      #m.addConstr(x_r[i] + quicksum(x_c[c] for c in inv_cov[i]) - y_r[i]  - quicksum(y_c[c] for c in inv_cov[i]) >= 1, 'const_%s' %(i))
      m.addConstr(x_r[i] + quicksum(x_c[c] for c in inv_cov[i]) - y_r[i]  - quicksum(y_c[c] for c in inv_cov[i]) + relax[i] >= 1, 'const_%s' %(i))
    else:
      #m.addConstr(quicksum(x_r[c] for c in F_r) + quicksum(x_c[c] for c in inv_cov[i]) - quicksum(y_r[c] for c in F_r) - quicksum(y_c[c] for c in inv_cov[i]) == 0, 'const_%s' %(i))
      m.addConstr(x_r[i]  + quicksum(x_c[c] for c in inv_cov[i]) - y_r[i]  - quicksum(y_c[c] for c in inv_cov[i]) <= 0, 'const_%s' %(i))

  #constraint for relax vars
  m.addConstr(quicksum(relax[i] for i in range(nrow)) <= relax_par, 'const_relax')
  m.ModelSense=1
  m.setParam( 'OutputFlag', False )
  m.optimize()
  return (row_name_mapx, row_name_mapy, col_name_mapx, col_name_mapy)



#m: gurobi model
#D is a 2d dictionary
#S is dictionary
#preclude combinations of columns by having high weights for them
def setcompress_neg_no_col(D, col_names, row_names, set_cols, set_rows, S, k, m, relax_par, coeff_pos_col_term, coeff_neg_col_term, verify):
  x_r={}; y_r={}; x_c={}; y_c={}; relax={}; col_name_mapx={}; col_name_mapy={};
  row_name_mapx={}; row_name_mapy={}; #coeff_neg_col_term=1
  nrow=len(D);
  #print col_names
  #print set_cols
  F_r = create_subsets_of_rows_given_subset(set_rows)
  F_c = create_subsets_of_cols(set_cols, k)
  inv_cov = coverage_w_set_rows(D, F_c, set_rows)
  #create variables
  for c in F_r:
    z = str(c)
    x_r[c] = m.addVar(obj = 1, vtype=GRB.BINARY, name = 'x_r_%s' %(z))
    row_name_mapx['x_r_'+z] = row_names[F_r[c]]
    y_r[c] = m.addVar(obj = 1, vtype=GRB.BINARY, name = 'y_r_%s' %(z))
    row_name_mapy['y_r_'+z] = row_names[F_r[c]]
  for c in F_c:
    z = var_str(F_c[c])
    #print F_c[c]
    z1 = var_str_with_col_names(F_c[c], col_names)
    #print "c=", F_c[c]
    #print "z=", z
    x_c[c] = m.addVar(obj = coeff_pos_col_term, vtype=GRB.BINARY, name = 'x_c%s' %(z))
    y_c[c] = m.addVar(obj = coeff_neg_col_term, vtype=GRB.BINARY, name = 'y_c%s' %(z))
    #col_name_mapx[x_c[c]] = z1
    col_name_mapx['x_c'+z] = z1
    #col_name_mapy[y_c[c]] = z1
    col_name_mapy['y_c'+z] = z1
  #add variables for relaxing constraints
  for i in set_rows:
    relax[i] = m.addVar(vtype=GRB.BINARY, name = 'relax_%s' %(i))
  #create constraints
  #print "S={}".format(S)
  for i in set_rows:
    if (S[i]):
      #m.addConstr(quicksum(x_r[c] for c in F_r) + quicksum(x_c[c] for c in inv_cov[i]) - quicksum(y_r[c] for c in F_r) - quicksum(y_c[c] for c in inv_cov[i]) >= 1, 'const_%s' %(i))
      #m.addConstr(x_r[i] + quicksum(x_c[c] for c in inv_cov[i]) - y_r[i]  - quicksum(y_c[c] for c in inv_cov[i]) >= 1, 'const_%s' %(i))
      #m.addConstr(x_r[i] + quicksum(x_c[c] for c in inv_cov[i]) - y_r[i]  - quicksum(y_c[c] for c in inv_cov[i]) + relax[i] >= 1, 'const_%s' %(i))
      m.addConstr(x_r[i] + quicksum(x_c[c] for c in inv_cov[i]) + relax[i] >= 1, 'const1_pos_%s' %(i))
      m.addConstr(y_r[i] + quicksum(y_c[c] for c in inv_cov[i]) == 0, 'const2_pos_%s' %(i))
    else:
      #m.addConstr(quicksum(x_r[c] for c in F_r) + quicksum(x_c[c] for c in inv_cov[i]) - quicksum(y_r[c] for c in F_r) - quicksum(y_c[c] for c in inv_cov[i]) == 0, 'const_%s' %(i))
      #m.addConstr(x_r[i]  + quicksum(x_c[c] for c in inv_cov[i]) - y_r[i]  - quicksum(y_c[c] for c in inv_cov[i]) <= 0, 'const_%s' %(i))
      for c1 in inv_cov[i]:
        m.addConstr(x_r[i] + quicksum(y_c[c2] for c2 in inv_cov[i]) - x_c[c1] >= 0, 'const_neg_%s_%s' %(i, c1))

  #constraint for relax vars
  m.addConstr(quicksum(relax[i] for i in set_rows) <= relax_par, 'const_relax')
  m.ModelSense=1
  m.setParam( 'OutputFlag', False )
  m.optimize()
  #verification
  #verify=1
  if verify:
    #print S
    print("S =", end= " ")
    for i in set_rows:
      if (S[i]): print(row_names[i], end=" ")
    print("\n")
    for c in F_c:
      #get rows corresponding to F_c[c]
      if (x_c[c].x ==1) or (y_c[c].x==1):
        print(var_str_with_col_names(F_c[c], col_names))
        for j in F_c[c]: print_col_entries(j, D, row_names, set_rows, col_names)
        print_set_of_col_entries(F_c[c], D, row_names, set_rows, col_names)
#        rows_corresponding_to_c=[]
#        for i in set_rows:
#          flag=1
#          for j in F_c[c]:
#            if (D[i][j]==0): flag=0
#          if flag: rows_corresponding_to_c.append(row_names[i])
#        print("var=", var_str_with_col_names(F_c[c], col_names), ":")
#        for k in rows_corresponding_to_c: print(k, end=" ")
#        print("\n")

  return (row_name_mapx, row_name_mapy, col_name_mapx, col_name_mapy)

def ilp_output(m, row_name_mapx, row_name_mapy, col_name_mapx, col_name_mapy, ofname=None):
  if ofname is not None:
    m.write(ofname)
  P={}; N={}
  for v in m.getVars():
    if (v.x == 1):
      #print("aaa", v)
      #print v.varName, v.x
      if ("x_r" in v.varName):
        P[v] = row_name_mapx[v.varName]
      if ("y_r" in v.varName):
        N[v] = row_name_mapy[v.varName]
      if ("x_c" in v.varName):
        P[v] = col_name_mapx[v.varName]
        #print "x_c"+col_name_mapx[v.varName], v.x
      if ("y_c" in v.varName):
        N[v] = col_name_mapy[v.varName]
        #print "y_c"+col_name_mapy[v.varName], v.x
      #else:
        #print v.varName, v.x
  print("positive:", end=" ")
  for v in P: print (P[v], end=" ")
  #print("\n")
  print("\nnegative:", end=" ")
  for v in N: print(N[v], end= " ")
  print("\n")

  return P, N

def init_D(nrow, ncol):
  #D=[[] for i in range(nrow)]
  D={}
  for i in range(nrow): D[i]={}
  if (nrow==4 and ncol==4):
    D[0] = {0:1, 1:1, 2:0, 3:1}
    D[1] = {0:1, 1:1, 2:0, 3:0}
    D[2] = {0:1, 1:0, 2:1, 3:1}
    D[3] = {0:0, 1:1, 2:1, 3:0}

    #D[0] = [1, 1, 0, 1]
    #D[1] = [1, 1, 0, 0]
    #D[2] = [1, 0, 1, 1]
    #D[3] = [0, 1, 1, 0]
  else:
    for i in range(nrow):
      for j in range(ncol):
        D[i][j]=random.randint(0, 1)
      #D[i] = [random.randint(0, 1) for j in range(ncol)]
  #print D
  for i in range(nrow):
    print("D[", i, "] = ", D[i])
  return D

def init_S(nrow):
  if (nrow==4):
    #S={0:1, 1:1, 2:0, 3:0}
    S={0:0, 1:1, 2:1, 3:0}
  else:
    S={}
    for i in range(nrow):
      S[i]=random.randint(0, 1)
  #print S
  return S

def get_col_names(fname):
  Dfreader = csv.reader(open(fname), delimiter = ',')
  line = next(Dfreader, None)
  col_names={}
  #col_names=[line[i] for i in range(1,len(line))]
  for i in range(1,len(line)):
    col_names[i] = line[i]
  return col_names

def get_row_names(fname):
  Dfreader = csv.reader(open(fname), delimiter = ',')
  line = next(Dfreader, None)
  row_names={}
  i=1
  for line in Dfreader:
    #row_names.append(line[0])
    row_names[i] = line[0]
    i +=1
  return row_names

def read_D_from_file(fname, leave_out_cols):
  Dfreader = csv.reader(open(fname), delimiter = ',')
  line = next(Dfreader, None)
  #ncol = len(line)-1
  set_cols={}
  for j in range(1, len(line)):
    if (j not in leave_out_cols):
      set_cols[j]=1
  D={}
  i=0
  for line in Dfreader:
    #D.append([])
    D[i]={}
    #for j in range(1, ncol+1):
      #D[i].append(int(float(line[j])))
    #D[i]=[int(float(line[j])) for j in range(1, ncol+1)]
    for j in set_cols: D[i][j] = int(float(line[j]))
    i += 1
  #for i in range(len(D)):
    #print "D[{}] = {}".format(i, D[i])
  return D

#set_cols and set_rows are dictionaries
def read_D_from_file_selected_cols_rows(fname, set_cols, set_rows):
  Dfreader = csv.reader(open(fname), delimiter = ',')
  line = next(Dfreader, None)
  #ncol = len(line)-1
  D={}
  i=1
  for line in Dfreader:
    if (i in set_rows):
      D[i]={}
      #for j in range(1, ncol+1):
        #D[i].append(int(float(line[j])))
      #D[i]=[int(float(line[j])) for j in range(1, ncol+1)]
      #print("i=", i, "line=", line)
      #print("D[", i, "]=", D[i])
      for j in set_cols: D[i][j] = int(float(line[j]))
    i +=1
  return D

#return the col in leave_out_cols
#assuming there is only one
def read_S_from_file(fname, leave_out_cols):
  Dfreader = csv.reader(open(fname), delimiter = ',')
  line = next(Dfreader, None)
  S={}; i=1
  #c=leave_out_cols.keys()[0]
  A=leave_out_cols.keys()
  c=list(A)[0]
  for line in Dfreader:
    S[i] = int(float(line[c]))
    i += 1
  return S

#return selected col_num, restricted to set_rows
def read_S_from_file_col_num(fname, col_num, set_rows):
  Dfreader = csv.reader(open(fname), delimiter = ',')
  line = next(Dfreader, None)
  S={}; i=1
  #c=leave_out_cols.keys()[0]
  for line in Dfreader:
    if (i in set_rows): S[i] = int(float(line[col_num]))
    i += 1
  return S

#ofname = "/home/vsakumar/narrative/data/row_ids"
def misc_func(fname, ofname):
  f=csv.reader(open(fname), delimiter = ',')
  line=next(f, next)
  g=open(ofname, 'w')
  i=1
  for line in f:
    z=str(i) + ' ' + line[0]+'\n'
    i +=1
    #print(z)
    g.write(z)

#D={}
#D[0] = {1:1, 2:0, 3:1}
#D[1] = {1:1, 2:1, 3:0}
#D[2] = {1:1, 2:1, 3:0}
#cols = {1:1, 2:1}
def pick_rows(cols_x, D_init):
  S={}
  for i in D_init:
    flag=1
    for j in cols_x:
      if (D_init[i][j]==0): flag=0
    if flag:
      S[i]=1
    else:
      S[i]=0
  return S

#D={}
#D[0] = {1:1, 2:0, 3:1}
#D[1] = {1:1, 2:1, 3:0}
#D[2] = {1:1, 2:1, 3:0}
#cols_x = {3:1}
def remove_cols(D_init, cols_x):
  D={}
  for i in D_init:
    D[i]={}
    for j in D_init[i]:
      if (j not in cols_x): D[i][j]=D_init[i][j]
  return D

#print(create_subsets_of_cols({0:1, 1:1, 2:1, 3:1, 4:1, 5:1}, k=6))

#if (scenario=='debug'):
#  # Model
#  m = Model("setcompress")
#  #test create_subsets_of_cols
#  #A=[1, 3, 4, 5]; k=3
#  #print(create_subsets_of_cols(A, k))
#  #test read_D_from_file_selected_rows_cols
#  fname = "/home/vsakumar/narrative/data/state_attr_new.csv"
#  ofname = "/home/vsakumar/narrative/data/row_ids"
#  set_cols={1:1, 2:1, 3:1, 4:1}
#  set_rows={1:1, 2:1}
#  #print(read_D_from_file_selected_cols_rows(fname, set_cols, set_rows))
#  #print(read_S_from_file_col_num(fname, 2, set_rows))
#  misc_func(fname, ofname)

def scenario_dummy(ofname):
  # Model
  m = Model("setcompress")
  nrow=4
  ncol=4
  k=2
  D=init_D(nrow, ncol)
  S=init_S(nrow)
  #print("S=", S)
  #set random col name
  col_names=[]
  for i in range(ncol):
    col_names.append('c'+str(i))
  row_names=[]
  for i in range(nrow):
    row_names.append('r'+str(i))
  (row_name_mapx, row_name_mapy, col_name_mapx, col_name_mapy) = setcompress(D, col_names, row_names, S, k, m, 0)
  ilp_output(m, row_name_mapx, row_name_mapy, col_name_mapx, col_name_mapy, ofname)

#not dummy input
# def scenario_readfile(ifname, ofname):
#   # Model
#   m = Model("setcompress")
#   k=2
#   fname = ifname
#   leave_out_cols={1:1}
#   D= read_D_from_file(fname, leave_out_cols)
#   S = read_S_from_file(fname, leave_out_cols)
#   col_names = get_col_names(fname)
#   row_names = get_row_names(fname)
#   (row_name_mapx, row_name_mapy, col_name_mapx, col_name_mapy) = setcompress(D, col_names, row_names, S, k, m, 0)
#   ilp_output(m, row_name_mapx, row_name_mapy, col_name_mapx, col_name_mapy, ofname)
# scenario_readfile("data/state_attr.csv", "readfile.lp")

#not dummy input
#def scenario_readfile_no_neg_cols(ifname, ofname):
#  # Model
#  m = Model("setcompress")
#  k=2
#  fname = ifname
#  set_cols={11:1, 12:1, 13:1, 14:1, 15:1, 16:1, 17:1, 18:1, 19:1, 20:1, 21:1, 22:1}
#  set_rows={}
#  for i in range(1, 52): set_rows[i]=1
#  D = read_D_from_file_selected_cols_rows(fname, set_cols, set_rows)
#  #print(D)
#  S=read_S_from_file_col_num(fname, 1, set_rows)
#  num_1_in_S=0
#  for i in S: num_1_in_S += S[i]
#  col_names = get_col_names(fname)
#  row_names = get_row_names(fname)
#  #print(row_names)
#  coeff_pos_col_term=1
#  coeff_neg_col_term=2
#  relax=4
#  (row_name_mapx, row_name_mapy, col_name_mapx, col_name_mapy) = setcompress_neg_no_col(D, col_names, row_names, set_cols, set_rows, S, k, m, relax, coeff_pos_col_term, coeff_neg_col_term, verify=0)
#  #print("mapped row names x", row_name_mapx)
#  #print("mapped row names y", row_name_mapy)
#  ilp_output(m, row_name_mapx, row_name_mapy, col_name_mapx, col_name_mapy, ofname)
#  print("------------------------------------------\n")
#scenario_readfile_no_neg_cols("data/state_attr.csv", "readfile.lp")


#loop over columns
def scenario_loop(ifname, ofname):
  k=2
  #fname = "/home/vsakumar/narrative/data/state_attr_new.csv"
  #set_cols={11:1, 12:1, 13:1, 14:1, 15:1, 16:1, 17:1, 18:1, 19:1, 20:1, 21:1, 22:1}
  fname = ifname
  set_cols={15:1, 16:1, 17:1, 18:1, 19:1, 20:1, 21:1, 22:1,
            23:1, 24:1, 25:1, 26:1, 27:1, 28:1, 29:1, 30:1, 31:1, 32:1, 33:1, 34:1,
            35:1, 36:1, 37:1, 38:1}
  set_rows={}
  for i in range(1, 52): set_rows[i]=1
  D = read_D_from_file_selected_cols_rows(fname, set_cols, set_rows)
  #print(D)
  cols_to_describe=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
  relax_frac_set = [0, 0.1, 0.2, 0.3]
  coeff_pos_col_term_set = [2]
  coeff_neg_col_term_set = [2, 4]
  for col in cols_to_describe:
    S=read_S_from_file_col_num(fname, col, set_rows)
    num_1_in_S=0
    for i in S: num_1_in_S += S[i]
    if num_1_in_S==0: continue
    col_names = get_col_names(fname)
    row_names = get_row_names(fname)
    coeff_pos_col_term=1
    coeff_neg_col_term=1
    for relax_frac in relax_frac_set:
      relax_par = int(relax_frac*num_1_in_S)
      for coeff_pos_col_term in coeff_pos_col_term_set:
        for coeff_neg_col_term in coeff_neg_col_term_set:
          # Model
          m = Model("setcompress")
          (row_name_mapx, row_name_mapy, col_name_mapx, col_name_mapy) = setcompress_neg_no_col(D, col_names, row_names, set_cols, set_rows, S, k, m, relax_par, coeff_pos_col_term, coeff_neg_col_term, verify=1)
          #print("row_name x", row_name_mapx)
          #print("relax_par", relax_par)
          print("describing col ", col_names[col], "relax ", relax_frac, "pos_coeff:", coeff_pos_col_term, "neg_coeff:", coeff_neg_col_term)
          ilp_output(m, row_name_mapx, row_name_mapy, col_name_mapx, col_name_mapy, ofname)
          #print("\n")
          print("------------------------------------------\n")

def scenario_all_combinations(ifname, ofname):
  ret = []

  # Model
  m = Model("setcompress")
  relax_frac_set = [0, 0.1, 0.2, 0.3]
  coeff_pos_col_term_set = [2]
  coeff_neg_col_term_set = [2, 4]
  k=2
  fname = ifname
  set_cols={1:1, 15:1, 16:1, 17:1, 18:1, 19:1, 20:1, 21:1, 22:1,
            23:1, 24:1, 25:1, 26:1, 27:1, 28:1, 29:1, 30:1, 31:1, 32:1, 33:1, 34:1,
            35:1, 36:1, 37:1, 38:1}
  groups_of_cols={}
  #groups_of_cols[0]={1:1, 2:1, 3:1, 4:1, 5:1, 6:1, 7:1, 8:1, 9:1, 10:1}
  groups_of_cols[0]={1:1}
  groups_of_cols[1]={15:1, 16:1, 17:1, 18:1} #was1
  groups_of_cols[2]={19:1, 20:1, 21:1, 22:1} #was2
  groups_of_cols[3]={23:1, 24:1, 25:1, 26:1} #was3
  groups_of_cols[4]={27:1, 28:1, 29:1, 30:1} #was4
  #groups_of_cols[5]={31:1, 32:1, 33:1, 34:1, 35:1, 36:1, 37:1, 38:1} #regions
  set_rows={}
  for i in range(1, 52): set_rows[i]=1
  #all combinations from set1 to set4
  all_subsets=create_subsets_of_cols_in_groups(groups_of_cols)
  D_prime = read_D_from_file_selected_cols_rows(fname, set_cols, set_rows)
  for s in all_subsets:
    S= pick_rows(all_subsets[s], D_prime)
    #construct D by dropping columns of all_subsets[s] from D_prime
    D=remove_cols(D_prime, all_subsets[s])
    set_cols_prime=set_cols.copy()
    for i in all_subsets[s]: set_cols_prime.pop(i)
    num_1_in_S=0
    for i in S: num_1_in_S += S[i]
    if num_1_in_S==0: continue
    col_names = get_col_names(fname)
    row_names = get_row_names(fname)
    for relax_frac in relax_frac_set:
      relax_par = int(relax_frac*num_1_in_S)
      for coeff_pos_col_term in coeff_pos_col_term_set:
        for coeff_neg_col_term in coeff_neg_col_term_set:
          # Model
          m = Model("setcompress")
          (row_name_mapx, row_name_mapy, col_name_mapx, col_name_mapy) = setcompress_neg_no_col(D, col_names, row_names, set_cols_prime, set_rows, S, k, m, relax_par, coeff_pos_col_term, coeff_neg_col_term, verify=0)
          #print("row_name x", row_name_mapx)
          #print("relax_par", relax_par)
          print("describing", end=" ")
          for r in all_subsets[s]: print(col_names[r], end=" ")
          print(": relax ", relax_frac, "pos_coeff:", coeff_pos_col_term, "neg_coeff:", coeff_neg_col_term)
          ret_P, ret_N = ilp_output(m, row_name_mapx, row_name_mapy, col_name_mapx, col_name_mapy, ofname)
          #print("\n")
          print("------------------------------------------\n")

          retobj = {
            "describing": [col_names[r] for r in all_subsets[s]],
            "relax": relax_frac,
            "pos_coeff": coeff_pos_col_term,
            "neg_coeff": coeff_neg_col_term,
            "positives": [str(ret_P[x]) for x in ret_P],
            "negatives": [str(ret_N[x]) for x in ret_N]
          }
          ret.append(retobj)

  return ret

if __name__ == "__main__":
    random.seed(1)
    from pprint import pprint
    pprint(scenario_all_combinations("data/state_attr_4wk.csv", "all_combinations.lp"))
