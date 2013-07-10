package main

import (
     "fmt"
    "os"
    "log"
    "syscall"
    "path/filepath"
    "time" 
)

func main() {
    var f *os.File
    var err error

    if len(os.Args) == 1 || os.Args[1] == "-h" || os.Args[1] == "--help" {
        fmt.Printf("usage: %s <file1> \n",filepath.Base(os.Args[0]))
        os.Exit(1)
    }

    if f, err = os.Open(os.Args[1]); err != nil {
        log.Println("failed to open the file: ", err)
        os.Exit(1)
    }
    fmt.Printf("File: %s\n---------\n", os.Args[1])

    var start trienode
    var words [][]byte = make([][]byte,200000)
    var startofstring int
    var j int
   
    programstart := time.Now()
    mappedData := mmapFile(f)
    for i := range mappedData.d {
        if mappedData.d[i] == '\n' {
            words[j] = mappedData.d[startofstring:i]
            addWord(&start, words[j])
            //fmt.Printf( "%s\n", words[j])
            startofstring = i + 1
            j++
        }
    }

	for w := range words {
		findwords(words[w],words[w])
	}

    delta := time.Now().Sub(programstart)
    fmt.Printf("Elapsed Time: %v\n", delta)
}
// An mmapData is mmap'ed read-only data from a file.
type mmapData struct {
    f *os.File
    d []byte
}

type trienode struct {
    words        int
    prefixes    int
    edges[26]    *trienode
}
var nodes []trienode = make([]trienode,10000000)
var trieindex int
func addWord( t *trienode, word []byte) *trienode {
    if len(word) == 0 {
        t.words = t.words + 1
    } else {
        t.prefixes = t.prefixes +1
         index  := word[0] - 'a'
        theRest := word[1:]
        if t.edges[index] == nil {
            t.edges[index] = &nodes[trieindex]
            trieindex++
        }
        t.edges[index] = addWord(t.edges[index], theRest)
    }
    return t
}

func findwords( word []byte, tail []byte) [
}

func mmapFile(f *os.File) mmapData {
        st, err := f.Stat()
        if err != nil {
                log.Fatal(err)
        }
        size := st.Size()
        if int64(int(size+4095)) != size+4095 {
                log.Fatalf("%s: too large for mmap", f.Name())
        }
        n := int(size)
        if n == 0 {
                return mmapData{f, nil}
        }
        data, err := syscall.Mmap(int(f.Fd()), 0, (n+4095)&^4095, syscall.PROT_READ, syscall.MAP_PRIVATE)
        if err != nil {
                log.Fatalf("mmap %s: %v", f.Name(), err)
        }
        return mmapData{f, data[:n]}
}
