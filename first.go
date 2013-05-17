package main
// Simple program that lists a file by mmapping the file and blasting it out
import (
   "fmt"
    "os"
    "log"
    "syscall"
    "path/filepath"
)

// An mmapData is mmap'ed read-only data from a file.
type mmapData struct {
		f *os.File
		d []byte
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
        data, err := syscall.Mmap(int(f.Fd()), 0, (n+4095)&^4095, syscall.PROT_READ, syscall.MAP_SHARED)
        if err != nil {
                log.Fatalf("mmap %s: %v", f.Name(), err)
        }
        return mmapData{f, data[:n]}
}



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

    mappedData := mmapFile(f)
    fmt.Printf("File: %s\n%s", os.Args[1], mappedData.d)
}
