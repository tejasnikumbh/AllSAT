import minisolvers
import numpy as np

'''
    Function to parse and forumlate a SAT Instance object that has methods
    such as .solve and .get_model to solve the sat instance
'''
def parse_SAT(stream):
    lines = stream.readlines()
    nVars = 0
    nClauses = 0
    S = minisolvers.MinisatSolver()
    cList = []
    for line in lines:
        line = line.rstrip()
        if(line.startswith('c') or 
            line.startswith('%') or 
            line.startswith('0') or
            line == ""):
            # The current line is boilerplate code
            pass
        elif(line.startswith('p')):
            # The current line the problems definition
            line = line.split()
            nVars = int(line[2])
            nClauses = int(line[3]) 
            for i in range(nVars): 
                S.new_var()  
        else:
            # The current line is a clause
            clause = [int(x) for x in line.split() if not(x == '0')]
            cList.append(clause)
            S.add_clause(clause)
    # Return the SAT Instance
    return [S,cList]
        
'''
    Returns the UCP Matrix for the minterm
'''            
def get_ucp_matrix(m_i,cList):
    # Transforming minterm to indicate the values of the terms
    m_i = [(i+1) if m_i[i] == 1 else -(i+1) for i in range(len(m_i))]
    
    # Populating the UCP Matrix
    ucp_matrix = []
    for clause in cList:
        ucp_row = []
        for literal in m_i:
            if(literal in clause):
                ucp_row.append(1)
            else:
                ucp_row.append(0)
        ucp_matrix.append(ucp_row)
    
    return [m_i,ucp_matrix]               

def get_essential_literals_and_modify(m_i,matrix):
    essentialI = get_essential_literals(matrix)
    clauses_covered_I = get_clauses_covered_I(essentialI,matrix)
    ucp_matrix_new = get_pruned_matrix(clauses_covered_I,matrix)            
    return [set([m_i[x] for x in essentialI]),
            ucp_matrix_new]

def get_essential_literals(matrix):
    essentialI = set([])
    for row in matrix:
        if(sum(row) == 1):  
            essentialI.add(row.index(1))            
    return essentialI
                                    
def get_clauses_covered_I(essentialI,matrix):
    clauses_covered = set([])
    for index in essentialI:
        for rowI in range(len(matrix)):
            if(matrix[rowI][index] == 1):
                clauses_covered.add(rowI)
    return clauses_covered                
            
def get_pruned_matrix(clauses_covered_I,ucp_matrix):
    ucp_matrix_new = []    
    for i in range(len(ucp_matrix)):
        if(i not in clauses_covered_I):
            ucp_matrix_new.append(ucp_matrix[i])
    return ucp_matrix_new
                
                
def prune_implied(matrix):
    row_elims = get_implied_rows(matrix)
    matrix = elim(matrix,row_elims)
    return matrix                
    
def elim(matrix,row_elims):
    new_matrix = []
    for i in range(len(matrix)):
        if(i not in row_elims):
            new_matrix.append(matrix[i])
    return new_matrix    
            
def get_implied_rows(matrix):
    rows_I = set([])
    for i in range(len(matrix)):
        other_set = set(range(len(matrix))) - set([i])
        for index in other_set:
            if(implied(index,i,matrix)):
                rows_I.add(index)            
    return rows_I

def implied(index,i,matrix):
    row1 = matrix[i]
    row2 = matrix[index]
    for i in range(len(row1)):
        if(row1[i] == 1):
            if(row2[i] == 0):
                return False    
    return True
    
def get_greedy_cover(m_i,ucp_matrix):
    cover_vars = set([])
    while(len(ucp_matrix) > 0):
        ucp_matrix_np = np.array(ucp_matrix)
        ucp_T = ucp_matrix_np.transpose()
        sumList = [sum(row) for row in ucp_T]
        max_val = max(sumList)
        max_val_I = sumList.index(max_val)
        cover_vars.add(max_val_I)
        ucp_matrix = prune_literal(max_val_I,ucp_matrix)       
    return set([m_i[i] for i in cover_vars])
    
def prune_literal(max_val_I,ucp_matrix):
    ucp_new = []
    for row in ucp_matrix:
        if(row[max_val_I] != 1):
            ucp_new.append(row)
    return ucp_new
            
def get_cube_cover(minterm,cList):
    [m_i,ucp_matrix] = get_ucp_matrix(minterm,cList)
    [e_lit,ucp_matrix] = get_essential_literals_and_modify(m_i,ucp_matrix)
    ucp_matrix = prune_implied(ucp_matrix)
    greedy_terms = get_greedy_cover(m_i,ucp_matrix)
    cube_cover = e_lit | greedy_terms
    blocking_clause = set([-x for x in cube_cover])
    return [cube_cover,blocking_clause]
        
'''
    Main Program for the SAT Instance algorithm
'''    
if __name__ == "__main__":
    
    # Parsing the Input in cnf form and forming a SAT Instance
    stream = open('input/input.cnf')
    [S,cList] = parse_SAT(stream)
    
    # F is updated every iteration while the initial clause list as in
    # cList remains the same. This is the crucial change that creates the 
    # DNF Cover faster. If we update cList each iteration, it will produce
    # disjoing cubes
    i = 1
    F = S
    Q = []
    while(F.solve()):
        minterm = list(F.get_model())
        [cube_cover,blocking_clause] = get_cube_cover(minterm,cList)
        Q.append(list(cube_cover))
        F.add_clause(blocking_clause)
        # Previous technique Used to produce disjoint cubes by uncommenting
        # the following line
        # cList.append(bloking_clause) 
        i = i + 1 
    
    if(i == 1):
        print "UNSATISFIABLE"
    else:
        print "SATISFIABLE"
        print "DNF Cover : ", Q      
    
       
