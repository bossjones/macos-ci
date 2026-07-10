JUST ?= just
.PHONY: up down build run logs ssh doctor test lint verify clean
up down build run logs ssh doctor test lint verify clean:
	@$(JUST) $@
%:
	@$(JUST) $@
