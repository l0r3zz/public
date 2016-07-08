package main

// Simple program that lists a file by mmapping the file and blasting it out
import (
	"fmt"
	"github.com/l0r3zz/gocode/mmapio"
	"log"
	"os"
	"path/filepath"
	"strconv"
	"time"
)

func main() {
	var f *os.File
	var err error
	var startofstring int
	var j int

	if len(os.Args) == 1 || os.Args[1] == "-h" || os.Args[1] == "--help" {
		fmt.Printf("usage: %s <file1> \n", filepath.Base(os.Args[0]))
		os.Exit(1)
	}

	if f, err = os.Open(os.Args[1]); err != nil {
		log.Println("failed to open the file: ", err)
		os.Exit(1)
	}

	fmt.Printf("File: %s\n", os.Args[1])

	time_programstart := time.Now()
	// Mmap the txt file in
	mappedData := mmapio.MmapFile(f)
	duration_aftermmap := time.Since(time_programstart)

	// Create a slice and read in the data
	var integers []int = make([]int, 100000)
	for i := range mappedData.D {
		if mappedData.D[i] == '\n' {
			integers[j], err = strconv.Atoi(string(mappedData.D[startofstring:i]))
			if err != nil {
				// handle error
				fmt.Println(err)
				os.Exit(2)
			}
			startofstring = i + 1
			j++
		}
	}

	duration_afteratoi := time.Since(time_programstart)

	fmt.Printf("MMap Operation: %v , Arrary conversion: %v\n",
		duration_aftermmap.String(),
		duration_afteratoi.String())

}
