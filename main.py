# Importing the standard libraries
import minisolvers
import time

'''
    Function : parse_SAT(stream)
    Function to parse and forumlate a SAT Instance object that has methods such 
    as .solve and .get_model to solve the sat instance. Parses the SAT problem
    from the standard DIMACS format for SAT Benchmarks
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
            clause = set([int(x) for x in line.split() if not(x == '0')])
            cList.append(clause)
            S.add_clause(clause)
    # Return the SAT Instance
    return [S,cList]
        
'''
    Function : get_ucp_matrix(m_i,cList)
    Returns the UCP Matrix for the minterm. This function is a part of formulat
    -ing the Hitting Set problem for the project and checks membership in the
    clause list that is provided
'''            
def get_ucp_matrix(m_i,cList):
    # Transforming minterm to indicate the values of the terms
    m_i = [(i+1) if m_i[i] == 1 else -(i+1) for i in range(len(m_i))]
    
    # Populating the UCP Matrix
    ucp_matrix = [0]*len(cList)
    for i in range(len(cList)):
	ucp_row = get_ucp_row(m_i,cList[i])    
        ucp_matrix[i] = ucp_row
    
    return [m_i,ucp_matrix]               

def get_ucp_row(m_i,clause):
    ucp_row = [0]*len(m_i) 
    for i in range(len(m_i)):
        if(m_i[i] in clause):
            ucp_row[i] = 1
    return ucp_row

'''
    Function : get_essential_literals_and_modify(m_i,matrix)
    Function returns the set of essential literals that are required for the
    set of clauses to be covered. Also modifies the matrix to eliminate the 
    covered set of clauses and returns it
'''
def get_essential_literals_and_modify(m_i,matrix):
    essentialI = get_essential_literals(matrix)
    clauses_covered_I = get_clauses_covered_I(essentialI,matrix)
    ucp_matrix_new = get_pruned_matrix(clauses_covered_I,matrix)            
    return [set([m_i[x] for x in essentialI]),
            ucp_matrix_new]

'''
    SubFunction : get_essential_literals(matrix)
    Returns the set of essential literals by checking the row sum of each of 
    the rows. Each row here is a clause in the SAT Instance     
'''
# TODO : Parallelizable function 
def get_essential_literals(matrix):
    essentialI = set([])
    for row in matrix:
        if(sum(row) == 1):  
            essentialI.add(row.index(1))            
    return essentialI

'''
    SubFunction : get_clauses_covered(essentialI,matrix)
    Returns the clauses covered by the essential literals since the essential
    literal will cover many clauses and not only the the clause that makes it 
    essential 
'''                                    
def get_clauses_covered_I(essentialI,matrix):
    clauses_covered = set([])
    for index in essentialI:
        for rowI in range(len(matrix)):
            if(matrix[rowI][index] == 1):
                clauses_covered.add(rowI)
    return clauses_covered                

'''
    Function : get_pruned_matrix(clauses_covered_I,ucp_matrix)
    Returns a new matrix by pruning the existing matrix by eliminating the 
    clauses that have already been covered        
'''            
def get_pruned_matrix(clauses_covered_I,ucp_matrix):
    ucp_matrix_new = []    
    for i in range(len(ucp_matrix)):
        if(i not in clauses_covered_I):
            ucp_matrix_new.append(ucp_matrix[i])
    return ucp_matrix_new
                
'''
    Function : prune_implied(matrix)
    Determines implied clauses and eliminates them. Note that this function 
    assumes that there are no repeated(same) clauses in the input instance. This
    should be the case as per the DIMACS guidelines
'''                
def prune_implied(matrix):
    row_elims = get_implied_rows(matrix)
    matrix = elim(matrix,row_elims)
    return matrix                
  
'''
    Function : elim(matrix,row_elims)
    Eliminates the particular set of rows from the matrix as per the reference
'''    
def elim(matrix,row_elims):
    new_matrix = []
    for i in range(len(matrix)):
        if(i not in row_elims):
            new_matrix.append(matrix[i])
    return new_matrix    

'''
    Function : get_implied_rows(matrix)
    Returns the set of implied rows or clauses from the given matrix. Performs
    the simple boolean implication test
'''            
def get_implied_rows(matrix):
    rows_I = set([])
    for i in range(len(matrix)):
        other_set = set(range(len(matrix))) - set([i])
        for index in other_set:
            if(implied(index,i,matrix)):
                rows_I.add(index)            
    return rows_I

'''
    Function : implied(index,i,matrix)
    Returns if row indexed by 'i' implied row indexed by 'index'
'''
def implied(index,i,matrix):
    row1 = matrix[i]
    row2 = matrix[index]
    for i in range(len(row1)):
        if(row1[i] == 1):
            if(row2[i] == 0):
                return False    
    return True
    
def transpose(matrix):
    return zip(*matrix)
	
'''
    Function : get_greedy_cover(m_i,ucp_matrix)
    This function returns the greedy set cover for the set cover problem. In 
    the current scenario, we prune the exiting ucp_matrix after every greedy 
    literal pick, until all the clauses have been exhausted
'''    
def get_greedy_cover(m_i,ucp_matrix):
    cover_vars = set([])
    while(len(ucp_matrix) > 0):
        ucp_T = transpose(ucp_matrix)
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

'''
    Function : get_cube_cover(minterm,cList)
    Returns the cube cover of a particular minterm and the associated blocking
    clause. Uses the SAT Instance defined by cList as the base for computing 
    the cube cover for the particular minterm
'''            
def get_cube_cover(minterm,cList):
    [m_i,ucp_matrix] = get_ucp_matrix(minterm,cList)
    [e_lit,ucp_matrix] = get_essential_literals_and_modify(m_i,ucp_matrix)
    ucp_matrix = prune_implied(ucp_matrix)
    greedy_terms = get_greedy_cover(m_i,ucp_matrix)
    cube_cover = e_lit | greedy_terms
    blocking_clause = set([-x for x in cube_cover])
    return [cube_cover,blocking_clause]

def print_result(i,Q):
    if(i == 1):
        print "UNSATISFIABLE"
    else:
        print "SATISFIABLE"
        

def get_cur_problem_stream(i):
    file_string = "input/Random3SAT/uf100-430/uf100-0" + str(i+1) + ".cnf"
    stream = open(file_string)
    return stream
        
        
def get_all_sat(S,cList):
    # F is updated every iteration while the initial clause list as in
    # cList remains the same. This is the crucial change that creates the 
    # DNF Cover faster. If we update cList each iteration, it will produce
    # disjoing cubes
    j = 1
    F = S
    Q = []
    while(F.solve()):
        minterm = list(F.get_model())
        [cube_cover,blocking_clause] = get_cube_cover(minterm,cList)
        Q.append(list(cube_cover))
        F.add_clause(blocking_clause)
        # Previous technique Used to produce disjoint cubes by uncommenting
        # the following line: - 
        # cList.append(bloking_clause) 
        j = j + 1 
    return [j,Q]
    
'''
    Main Program for the SAT Instance algorithm. This function is incharge of
    which SAT Benchmark the algorithm is tried upon and produces the required 
    results
'''    
if __name__ == "__main__":
    
    # Parsing the Input in cnf form and forming a SAT Instance
    for i in range(100):
        print "Current problem : " + str(i)
        stream = get_cur_problem_stream(i)
        [S,cList] = parse_SAT(stream)
        [j,Q] = get_all_sat(S,cList)
        print_result(j,Q)

                  
   

