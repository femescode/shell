package main

import (
	"bufio"
	"bytes"
	"context"
	"encoding/json"
	"flag"
	"fmt"
	"io/ioutil"
	"log"
	"net/http"
	"os"
	"os/signal"
	"regexp"
	"sort"
	"strings"
	"sync"
	"sync/atomic"
	"syscall"
	"time"

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
	t.last_err = nil
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
		fmt.Printf("%s qps:%d, ok:%d, error:%d, avg:(%.2fms), p95:(%.2fms), p99:(%.2fms), max:(%.2fms) %s\n",
			time.Now().Format("2006-01-02 15:04:05"), qps, ok_cnt, error_cnt, float64(avg.Microseconds())/1e3, float64(p95.Microseconds())/1e3, float64(p99.Microseconds())/1e3, float64(max.Microseconds())/1e3, err_str)
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

func verboseAny(prefix string, v any) {
	switch v.(type) {
	case string:
		fmt.Fprintln(os.Stderr, prefix+v.(string))
	case *string:
		fmt.Fprintln(os.Stderr, prefix+*(v.(*string)))
	default:
		dataBytes, _ := json.Marshal(v)
		fmt.Fprintln(os.Stderr, prefix+string(dataBytes))
	}
}

func httpRequest(_httpCli *http.Client, params *RequestParams) (string, error) {
	var request *http.Request
	var err error
	if params.Body == "" {
		request, err = http.NewRequest("GET", params.URL, nil)
	} else {
		request, err = http.NewRequest("POST", params.URL, bytes.NewBufferString(params.Body))
	}

	if err != nil {
		return "", fmt.Errorf("http.NewRequest failed %v: %w", params.URL, err)
	}
	if _, ok := params.Headers["Content-Type"]; !ok {
		params.Headers["Content-Type"] = "application/x-www-form-urlencoded; charset=UTF-8"
	}
	for k, v := range params.Headers {
		request.Header.Set(k, v)
	}

	response, err := _httpCli.Do(request)
	if err != nil {
		return "", fmt.Errorf("httpCli.Do failed: %w", err)
	}
	defer response.Body.Close()

	respBytes, err := ioutil.ReadAll(response.Body)
	if err != nil {
		return "", fmt.Errorf("ioutil.ReadAll failed: %w", err)
	}

	bodystr := string(respBytes)
	return bodystr, nil
}

type RequestParams struct {
	URL     string
	Headers map[string]string
	Body    string
}

func splitByWhitespace(s string) []string {
	return strings.FieldsFunc(s, func(r rune) bool {
		return r == ' ' || r == '\t' || r == '\n' || r == '\r'
	})
}

func parseRequestLine(line string) (*RequestParams, error) {
	args := splitByWhitespace(line)
	params := &RequestParams{
		Headers: make(map[string]string),
	}

	fs := flag.NewFlagSet("httpRequest", flag.ContinueOnError)
	var headers []string
	fs.Func("H", "Request headers (e.g. 'content-type:application/json')", func(s string) error {
		headers = append(headers, s)
		return nil
	})
	body := fs.String("d", "", "Request body")

	// 重新解析参数
	err := fs.Parse(args)
	if err != nil {
		return nil, err
	}

	// 检查必填URL
	if params.URL == "" {
		// 尝试从非标志参数获取URL
		for _, arg := range args {
			if !strings.HasPrefix(arg, "-") && strings.HasPrefix(arg, "http") {
				params.URL = arg
				break
			}
		}
		if params.URL == "" {
			return nil, fmt.Errorf("URL is required")
		}
	}

	// 处理头部
	for _, header := range headers {
		parts := strings.SplitN(header, ":", 2)
		if len(parts) != 2 {
			return nil, fmt.Errorf("invalid header format")
		}
		params.Headers[strings.TrimSpace(parts[0])] = strings.TrimSpace(parts[1])
	}

	// 处理请求体
	if *body != "" {
		params.Body = *body
	}
	return params, nil
}

func main() {
	var filepath string
	flag.StringVar(&filepath, "f", "", "filepath. ")
	var workers int64
	flag.Int64Var(&workers, "t", 50, "worker thread num. (required)")
	var qps float64
	flag.Float64Var(&qps, "q", 0, "qps. (required)")
	var headers []string
	flag.Func("H", "Request headers (e.g. 'content-type:application/json')", func(s string) error {
		headers = append(headers, s)
		return nil
	})
	body := flag.String("d", "", "Request body")
	verbose := flag.Bool("v", false, "verbose")
	flag.Usage = func() {
		fmt.Fprintf(os.Stderr, "Usage: %s [OPTIONS] url \n", os.Args[0])
		flag.PrintDefaults()
	}
	flag.Parse()
	if workers == 0 || qps == 0 {
		flag.Usage()
		os.Exit(2)
	}

	args := flag.Args()
	urlstr := ""
	if len(args) == 0 {
		if filepath == "" {
			urlstr = get_multi_input("Enter url:>> \n")
			fmt.Println("<< Execute url begin...")
		}
	} else {
		urlstr = args[0]
	}

	var _httpCli = &http.Client{
		Timeout: time.Duration(50) * time.Second,
		Transport: &http.Transport{
			MaxIdleConnsPerHost:   int(workers),
			MaxConnsPerHost:       int(workers),
			IdleConnTimeout:       90 * time.Second,
			TLSHandshakeTimeout:   10 * time.Second,
			ExpectContinueTimeout: 1 * time.Second,
		},
	}

	init := func() interface{} {
		return nil
	}

	var file *os.File
	var scanner *bufio.Scanner
	var mu sync.Mutex
	getRequestParams := func() (*RequestParams, error) {
		if urlstr != "" {
			params := &RequestParams{
				URL:     urlstr,
				Headers: make(map[string]string),
				Body:    *body,
			}
			for _, header := range headers {
				parts := strings.SplitN(header, ":", 2)
				if len(parts) != 2 {
					return nil, fmt.Errorf("invalid header format")
				}
				params.Headers[strings.TrimSpace(parts[0])] = strings.TrimSpace(parts[1])
			}
			return params, nil
		} else {
			mu.Lock()
			defer mu.Unlock()
			for {
				// 第一次或文件遍历完，重新打开文件
				if scanner == nil || !scanner.Scan() {
					if scanner != nil {
						if err := scanner.Err(); err != nil {
							log.Println(err)
						}
						file.Close()
					}
					f, err := os.Open(filepath)
					if err != nil {
						log.Fatal(err)
						return nil, err
					}
					file = f
					scanner = bufio.NewScanner(file)
				}
				// 读取下一行
				line := scanner.Text()
				if strings.TrimSpace(line) != "" {
					return parseRequestLine(line)
				}
			}
		}
	}

	callback := func(task_param interface{}) error {
		request, err := getRequestParams()
		if err != nil {
			return err
		}
		if *verbose {
			verboseAny("Request: ", request)
		}

		body, err := httpRequest(_httpCli, request)
		if *verbose {
			verboseAny("Body: ", body)
		}
		return err
	}
	go_limiter_exec(workers, qps, init, callback)
}
