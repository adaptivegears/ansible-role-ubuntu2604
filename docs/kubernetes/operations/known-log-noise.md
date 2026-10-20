# Kubernetes log triage

Check API readiness before treating a log message as benign:

```bash
kubectl --kubeconfig /etc/kubernetes/admin.conf get --raw '/readyz?verbose'
```

| Pattern | Usually benign when | Investigate when |
|---|---|---|
| etcd `127.0.0.1:2379` dial or handshake: `operation was canceled` / `context canceled` | Periodic gRPC health-probe cancellation; API remains ready ([upstream issue](https://github.com/kubernetes/kubernetes/issues/134080)) | `i/o timeout`, `context deadline exceeded`, failed requests, or etcd readiness failure |
| `metrics.k8s.io` connection refused / HTTP 503 | Briefly after boot, before metrics-server is ready | Errors persist after pod startup or `kubectl top nodes` fails |
| `quota admission added evaluator for:` | Informational lazy evaluator registration | Not an error by itself |
| Kubelet TCP/10250 `broken pipe` / WebSocket close 1006 | A client ends exec, attach, logs, or port-forward streams | Operations fail for users or reset rates rise without matching client activity |
