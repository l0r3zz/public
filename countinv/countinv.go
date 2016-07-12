package main

// Simple program that exercises the count inversion algorithm in go
import (
	"fmt"
	"github.com/l0r3zz/gocode/mmapio"
	"log"
	"os"
	"path/filepath"
	"strconv"
	"time"
)

func countinv(buffer []int) (int, []int) {

	if len(buffer) <= 1 {
		return 0, buffer
	}

	var (
		a_inv int
		b_inv int
		a     []int
		b     []int
	)
	var invcnt int // holds the inversion count to be returned

	c := make([]int, len(buffer))

	a_inv, a = countinv(buffer[0 : len(buffer)/2])
	b_inv, b = countinv(buffer[len(buffer)/2:])

	// Merge the result
	var j int
	var k int

	for i := range c {
		if j == len(a) {
			c[i] = b[k]
			k++
			continue
		}
		if k == len(b) {
			c[i] = a[j]
			j++
			continue
		}
		if a[j] < b[k] {
			c[i] = a[j]
			j++
		} else {
			c[i] = b[k]
			k++
			invcnt = invcnt + (len(a) - j)
		}
	}

	invcnt = invcnt + a_inv + b_inv
	return invcnt, c
}

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
	var integers []int = make([]int, 0, 200000)
	var m int

	for i := range mappedData.D {
		if mappedData.D[i] == '\n' {
			m, err = strconv.Atoi(string(mappedData.D[startofstring:i]))
			if err != nil {
				// handle error
				fmt.Println(err)
				os.Exit(2)
			}
			integers = append(integers, m)
			startofstring = i + 1
			j++
		}
	}

	fmt.Printf("Size of integers: %v\n", len(integers))

	duration_afteratoi := time.Since(time_programstart)
	inversions, result := countinv(integers)
	duration_aftercountinv := time.Since(time_programstart)
	fmt.Printf("MMap Operation: %v , Arrary conversion: %v Mergesort: %v\n",
		duration_aftermmap.String(),
		duration_afteratoi.String(),
		duration_aftercountinv.String())
	j = result[0] // just here to surpress complaints about unnused result array
	fmt.Printf("Inversions: %v\n", inversions)
	//	fmt.Printf("Integers: \n")
	//	for i := range result {
	//		fmt.Printf("%v\n", result[i])
	//	}

}
