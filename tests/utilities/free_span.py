def free(spans, neg):
    n_start, n_length = neg
    n_end = n_start + n_length
    out = []
    for start, length in spans:
        end = start + length
        if n_start <= start < end <= n_end:
                continue # eclipsed by neg
        else:
            if start < n_start:
                c_end = min([end, n_start])
                out.append((start, c_end - start)) # fore segment
            if n_end < end: # if not elif because both are possible
                c_start = max([start, n_end])
                out.append((c_start, end - c_start)) # aft segment
    return out

if __name__ == "__main__":
    Ss1 = [(0, 9)]

    A = (0, 3) # overlaps and touches head
    B = (6, 3) # overlaps and touches tail
    C = (-4, 1) # before head no overlap
    D = (12, 1) # after tail no overlap
    E = (0, 9)  # same as contents
    F = (-1, 12) # overlaps all no touching
    G = (-1, 3) # overlaps head no touching
    H = (8, 3) # overlaps tail no touching

    print(free(Ss1, A)) # 3, 6
    print(free(Ss1, B)) # 0, 6
    print(free(Ss1, C)) # 0, 9
    print(free(Ss1, D)) # 0, 9
    print(free(Ss1, E)) # nothing
    print(free(Ss1, F)) # nothing
    print(free(Ss1, G)) # 2, 7
    print(free(Ss1, H)) # 0, 8

    print("-" * 20)
    Ss2 = [(0, 3), (3, 3), (6, 3)]

    print(free(Ss2, A)) # (3, 3), (6, 3) FAIL
    print(free(Ss2, B)) # (0, 3), (3, 3) FAIL
    print(free(Ss2, C)) # (0, 3), (3, 3), (6, 3) FAIL
    print(free(Ss2, D)) # (0, 3), (3, 3), (6, 3) FAIL
    print(free(Ss2, E)) # nothing
    print(free(Ss2, F)) # nothing
    print(free(Ss2, G)) # (2, 1), (3, 3), (6, 3) FAIL
    print(free(Ss2, H)) # (0, 3), (3, 3), (6, 2) FAIL
    
