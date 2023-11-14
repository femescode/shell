package main

import (
	"bufio"
	"context"
	"database/sql"
	"flag"
	"fmt"
	"log"
	"os"
	"os/signal"
	"regexp"
	"sort"
	"strings"
	"sync"
	"sync/atomic"
	"syscall"
	"time"

	_ "github.com/go-sql-driver/mysql"
	"golang.org/x/crypto/ssh/terminal"
	"golang.org/x/time/rate"
)

type Timer struct {
	mu              sync.Mutex
	ok_cnt          int
	error_cnt       int
	durations       []time.Duration
	ok_duration_sum time.Duration
	last_err        error
}

func (t *Timer) Record(d time.Duration, err error) {
	t.mu.Lock()
	defer t.mu.Unlock()
	if err == nil {
		t.ok_cnt++
		t.durations = append(t.durations, d)
		t.ok_duration_sum += d
	} else {
		t.error_cnt++
		t.last_err = err
	}
}

func (t *Timer) CalAndClear() (int, int, error, time.Duration, time.Duration, time.Duration, time.Duration) {
	t.mu.Lock()
	defer t.mu.Unlock()
	ok_cnt := t.ok_cnt
	error_cnt := t.error_cnt
	last_err := t.last_err
	if len(t.durations) == 0 {
		t.Clear()
		return ok_cnt, error_cnt, last_err, 0, 0, 0, 0
	}
	sort.Slice(t.durations, func(i, j int) bool {
		return t.durations[i] < t.durations[j]
	})
	avg := t.ok_duration_sum / time.Duration(t.ok_cnt)
	idx := int(float64(len(t.durations)) * 0.95)
	p95 := t.durations[idx]
	idx99 := int(float64(len(t.durations)) * 0.99)
	p99 := t.durations[idx99]
	max := t.durations[len(t.durations)-1]

	// clear record
	t.Clear()

	return ok_cnt, error_cnt, last_err, avg, p95, p99, max
}

func (t *Timer) Clear() {
	t.ok_cnt = 0
	t.error_cnt = 0
	t.durations = []time.Duration{}
	t.ok_duration_sum = 0
}

func go_limiter_exec(workers int64, qps float64, init func() interface{}, callback func(item interface{}) error) {
	var counter int64 = 0
	timer := &Timer{}
	limiter := rate.NewLimiter(rate.Limit(qps), 1)
	for i := int64(0); i < workers; i++ {
		param := init()
		go func(task_param interface{}) {
			for {
				err := limiter.Wait(context.Background())
				if err != nil {
					log.Printf("rate limit error: %v", err)
					continue
				}
				start := time.Now()
				err = callback(task_param)
				end := time.Now()

				timer.Record(end.Sub(start), err)
				atomic.AddInt64(&counter, 1)
			}
		}(param)
	}
	go func() {
		// 创建一个信号通道
		sigs := make(chan os.Signal, 1)
		// 监听 SIGINT 信号
		signal.Notify(sigs, syscall.SIGINT)
		// 等待信号
		<-sigs
		// 输出消息并退出程序
		// fmt.Println("程序已中断")
		os.Exit(0)
	}()

	ticker := time.Tick(time.Second)
	for range ticker {
		// 每秒执行一次的操作
		qps := atomic.SwapInt64(&counter, 0)
		ok_cnt, error_cnt, last_err, avg, p95, p99, max := timer.CalAndClear()
		err_str := ""
		if last_err != nil {
			err_str = last_err.Error()
		}
		fmt.Printf("qps:%d, ok:%d, error:%d, avg:(%.2fms), p95:(%.2fms), p99:(%.2fms), max:(%.2fms) %s\n",
			qps, ok_cnt, error_cnt, float64(avg.Microseconds())/1e3, float64(p95.Microseconds())/1e3, float64(p99.Microseconds())/1e3, float64(max.Microseconds())/1e3, err_str)
	}
}

func get_multi_input(promot string) string {
	fmt.Print(promot)
	scanner := bufio.NewScanner(os.Stdin)
	lines := []string{}
	empty_num := 0
	for scanner.Scan() {
		if err := scanner.Err(); err != nil {
			panic(err.Error())
		}
		line := scanner.Text()
		if line != "" {
			lines = append(lines, line)
			empty_num = 0
			re := regexp.MustCompile(`;\s*$`)
			if re.MatchString(line) {
				break
			}
		} else {
			empty_num = empty_num + 1
		}
		if empty_num >= 3 {
			break
		}
	}
	return strings.Join(lines, "\n")
}

func main() {
	var host string
	flag.StringVar(&host, "H", "", "host. (required)")
	var port int
	flag.IntVar(&port, "P", 0, "port. (required)")
	var user string
	flag.StringVar(&user, "u", "", "user. (required)")
	var password string
	flag.StringVar(&password, "p", "", "password.")
	var database string
	flag.StringVar(&database, "D", "", "database. (required)")
	var workers int64
	flag.Int64Var(&workers, "t", 50, "worker thread num. (required)")
	var qps float64
	flag.Float64Var(&qps, "q", 0, "qps. (required)")
	flag.Usage = func() {
		fmt.Fprintf(os.Stderr, "Usage: %s [OPTIONS] sql \n", os.Args[0])
		flag.PrintDefaults()
	}
	flag.Parse()

	if host == "" || port == 0 || user == "" || database == "" || workers == 0 || qps == 0 {
		flag.Usage()
		os.Exit(2)
	}

	if password == "" {
		fmt.Print("Enter password: ")
		bytePassword, err := terminal.ReadPassword(int(syscall.Stdin))
		if err != nil {
			panic(err.Error())
		}
		password = string(bytePassword)
		fmt.Println(strings.Repeat("*", len(password)))
	}

	args := flag.Args()
	sqlstr := ""
	if len(args) == 0 {
		sqlstr = get_multi_input("Enter sql:>> \n")
		fmt.Println("<< Execute sql begin...")
	} else {
		sqlstr = args[0]
	}

	init := func() interface{} {
		// 连接MySQL数据库
		dataSourceName := fmt.Sprintf("%s:%s@tcp(%s:%d)/%s", user, password, host, port, database)
		db, err := sql.Open("mysql", dataSourceName)
		if err != nil {
			panic(err.Error())
		}
		return db
	}

	callback := func(task_param interface{}) error {
		db := task_param.(*sql.DB)
		// 执行SQL查询
		rows, err := db.Query(sqlstr)
		if err != nil {
			return err
		}
		defer rows.Close()
		return nil
	}
	go_limiter_exec(workers, qps, init, callback)
}
