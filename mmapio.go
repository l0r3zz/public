package mmapio

// Simple program that lists a file by mmapping the file and blasting it out
import (
	"log"
	"os"
	"syscall"
)

// An mmapData is mmap'ed read-only data from a file.
type MmapData struct {
	F *os.File
	D []byte
}

func MmapFile(f *os.File) MmapData {
	st, err := f.Stat()
	if err != nil {
		log.Fatal(err)
	}
	size := st.Size()
	if int64(int(size+4095)) != size+4095 {
		log.Fatal("%s: too large for mmap", f.Name())
	}
	n := int(size)
	if n == 0 {
		return MmapData{f, nil}
	}
	data, err := syscall.Mmap(int(f.Fd()), 0, (n+4095)&^4095,
		syscall.PROT_READ, syscall.MAP_SHARED)
	if err != nil {
		log.Fatal("mmap %s: %v", f.Name(), err)
	}
	return MmapData{f, data[:n]}
}
