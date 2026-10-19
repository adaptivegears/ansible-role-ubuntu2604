# Known log noise

Log patterns that appear on a healthy cluster built by this role and look
alarming but are verified benign. Each entry lists the signature, the cause,
and the signal that would make the same pattern a real problem.

Baseline health check before triaging any apiserver log line:

```bash
kubectl --kubeconfig /etc/kubernetes/admin.conf get --raw /readyz?verbose
```

## etcd client dial warning every minute

**Signature** (kube-apiserver, warning level, exactly once per 60s, channel
number incrementing each time):

```text
W... logging.go:55] [core] [Channel #NNNN SubChannel #NNNN]grpc: addrConn.createTransport
failed to connect to {Addr: "127.0.0.1:2379", ...pickfirstleaf...}.
Err: connection error: desc = "transport: Error while dialing: dial tcp 127.0.0.1:2379:
operation was canceled"
```

A variant reads `authentication handshake failed: context canceled`.

**Cause**: upstream log spam from the gRPC `pickfirstleaf` balancer in the
apiserver's etcd client (Kubernetes 1.34+). A periodic health probe creates a
fresh client, finishes, and cancels its own in-flight dial; gRPC logs the
abandoned dial as a connection error. Tracked in
[kubernetes/kubernetes#134080](https://github.com/kubernetes/kubernetes/issues/134080).
There is no configuration knob to silence it.

**Real problem instead when**: the error text is `i/o timeout` or requests fail
with `context deadline exceeded`, or `/readyz` reports etcd not ok. That
indicates genuine loopback/etcd connectivity loss, not canceled probes.

## Aggregated metrics API errors right after boot

**Signature** (kube-apiserver, first ~30s after a reboot):

```text
E... remote_available_controller.go:...] "Unhandled Error" err="v1beta1.metrics.k8s.io
failed with: ... connect: connection refused"
E... controller.go:...] Error updating APIService "v1beta1.metrics.k8s.io" ...
ResponseCode: 503 ... "no RequestInfo found in the context"
```

**Cause**: the aggregation layer probes the registered `metrics.k8s.io`
APIService as soon as the apiserver starts, before the metrics-server pod is
ready. The burst ends with `Adding GroupVersion metrics.k8s.io v1beta1 to
ResourceManager` once the pod answers.

**Real problem instead when**: the errors continue past pod startup or
`kubectl top nodes` fails. Then inspect the metrics-server deployment.

## Quota admission evaluator lines after restart

**Signature** (kube-apiserver, info level, spread over the first hour after a
restart):

```text
I... controller.go:667] quota admission added evaluator for: <resource>
```

**Cause**: the quota admission plugin registers evaluators lazily, the first
time each resource type is created or updated after an apiserver restart.
Purely informational.

**Real problem**: never, by itself.

## Kubelet proxy stream resets

**Signature** (kube-apiserver, ongoing at low rate):

```text
E... upgradeaware.go:...] Error proxying data from client to backend:
write tcp <node-ip>:NNNNN-><node-ip>:10250: write: broken pipe
E... upgradeaware.go:...] Error proxying data from client to backend:
websocket: close 1006 (abnormal closure): unexpected EOF
```

**Cause**: port 10250 is the kubelet. These are `exec`, `attach`, `logs
--follow`, and `port-forward` streams proxied through the apiserver whose
client ended the connection abruptly — normal for automation that execs into
pods or follows logs and then hangs up.

**Real problem instead when**: paired with user-visible failures of the same
operations (exec/logs/port-forward not working), or the rate jumps without a
matching change in automation activity.
