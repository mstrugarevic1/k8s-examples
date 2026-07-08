.PHONY: apply setup test-good test-bad clean

apply:
	kubectl apply -f policies/

setup:
	kubectl apply -f examples/setup.yaml

test-good: setup
	kubectl apply -f examples/good/

test-bad: setup
	@for f in examples/bad/*.yaml; do \
		echo "Testing $$f (expected to fail)..."; \
		kubectl apply -f $$f 2>&1 | grep -q "denied by" && echo "PASS: $$f rejected" || echo "FAIL: $$f allowed"; \
	done

clean:
	kubectl delete -f examples/good/ --ignore-not-found
	kubectl delete -f examples/setup.yaml --ignore-not-found
	kubectl delete -f policies/ --ignore-not-found
