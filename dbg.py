import collections, sys
from Bio import Seq, SeqIO, SeqRecord


def twin(km):
    return Seq.reverse_complement(km)

def kmers(seq,k):
    for i in xrange(len(seq)-k+1):
        yield seq[i:i+k]

def fw(km):
    for x in 'ACGT':
        yield km[1:]+x

def bw(km):
    for x in 'ACGT':
        yield x + km[:-1]


def build(fn,k=31,limit=1):
    d = collections.defaultdict(int)

    for f in fn:
        reads = SeqIO.parse(f,'fastq')
        for read in reads:
            seq_s = str(read.seq)
            seq_l = seq_s.split('N')
            for seq in seq_l:
                for km in kmers(seq,k):
                    d[km] +=1
                seq = twin(seq)
                for km in kmers(seq,k):
                    d[km] += 1

    d1 = [x for x in d if d[x] <= limit]
    for x in d1:
        del d[x]

    return d

def contig_to_string(c):
    return c[0] + ''.join(x[-1] for x in c[1:])

def get_contig(d,km):
    c_fw = get_contig_forward(d,km)
    
    c_bw = get_contig_forward(d,twin(km))

    if km in fw(c_fw[-1]):
        c = c_fw
    else:
        c = [twin(x) for x in c_bw[-1:0:-1]] + c_fw
    return contig_to_string(c),c
        

def get_contig_forward(d,km):
    c_fw = [km]
    
    while True:
        if sum(x in d for x in fw(c_fw[-1])) != 1:
            break
        
        cand = [x for x in fw(c_fw[-1]) if x in d][0]
        if cand == km or cand == twin(km):
            break # break out of cycles or mobius contigs
        if cand == twin(c_fw[-1]):
            break # break out of hairpins
        
        if sum(x in d for x in bw(cand)) != 1:
            break

        c_fw.append(cand)

    return c_fw

def all_contigs(d,k):
    done = set()
    r = []
    for x in d:
        if x not in done:
            s,c = get_contig(d,x)
            for y in c:
                done.add(y)
                done.add(twin(y))
            r.append(s)
    
    G = {}
    heads = {}
    tails = {}
    for i,x in enumerate(r):
        G[i] = ([],[])
        heads[x[:k]] = (i,'+')
        tails[twin(x[-k:])] = (i,'-')
    
    for i in G:
        x = r[i]
        for y in fw(x[-k:]):
            if y in heads:
                G[i][0].append(heads[y])
            if y in tails:
                G[i][0].append(tails[y])
        for z in fw(twin(x[:k])):
            if z in heads:
                G[i][1].append(heads[z])
            if z in tails:
                G[i][1].append(tails[z])

    return G,r

    

def print_GFA(G,cs,k):
    print "H  VN:Z:1.0"
    for i,x in enumerate(cs):
        print "S\t%d\t%s\t*"%(i,x)
        
    for i in G:
        for j,o in G[i][0]:
            print "L\t%d\t+\t%d\t%s\t%dM"%(i,j,o,k-1)
        for j,o in G[i][1]:
            print "L\t%d\t-\t%d\t%s\t%dM"%(i,j,o,k-1)
    


if __name__ == "__main__":
    k = int(sys.argv[1])
    d = build(sys.argv[2:],k,1)
    G,cs = all_contigs(d,k)
    print_GFA(G,cs,k)
