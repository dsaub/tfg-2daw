#!/bin/bash

set -u

readonly HOSTS=(
	"aws-docker-mysql"
	"aws-docker-redis"
	"aws-docker-celery"
	"aws-docker"
)

readonly WAIT_SECONDS=5
readonly REMOTE_DEPLOY_DIR="/root/deploys"

usage() {
	echo "Uso: $0 {start|stop|restart|update}"
}

print_status() {
	local action="$1"
	local host="$2"
	local status="$3"

	# Estilo similar al output de OpenRC.
	printf "* %-8s %-16s [%s]\n" "$action" "$host" "$status"
}

run_remote_compose() {
	local host="$1"
	local command="$2"

	ssh -o BatchMode=yes -o LogLevel=ERROR -T "$host" "sudo -n sh -c \"cd '$REMOTE_DEPLOY_DIR' || exit 1; if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then docker compose $command; elif command -v docker-compose >/dev/null 2>&1; then docker-compose $command; else exit 1; fi\"" >/dev/null 2>&1
}

run_for_all_hosts() {
	local mode="$1"
	local host=""
	local i=0
	local total=${#HOSTS[@]}

	for host in "${HOSTS[@]}"; do
		case "$mode" in
			start)
				if run_remote_compose "$host" "up -d"; then
					print_status "Started" "$host" "ok"
				else
					print_status "Started" "$host" "fail"
					exit 1
				fi
				;;
			stop)
				if run_remote_compose "$host" "down"; then
					print_status "Stopped" "$host" "ok"
				else
					print_status "Stopped" "$host" "fail"
					exit 1
				fi
				;;
			restart)
				if run_remote_compose "$host" "down" && run_remote_compose "$host" "up -d"; then
					print_status "Restarted" "$host" "ok"
				else
					print_status "Restarted" "$host" "fail"
					exit 1
				fi
				;;
			update)
				if run_remote_compose "$host" "pull" && run_remote_compose "$host" "down" && run_remote_compose "$host" "up -d"; then
					print_status "Updated" "$host" "ok"
				else
					print_status "Updated" "$host" "fail"
					exit 1
				fi
				;;
			*)
				usage
				exit 1
				;;
		esac

		i=$((i + 1))
		if [ "$i" -lt "$total" ]; then
			sleep "$WAIT_SECONDS"
		fi
	done
}

if [ "$#" -ne 1 ]; then
	usage
	exit 1
fi

case "$1" in
	start|stop|restart|update)
		run_for_all_hosts "$1"
		;;
	*)
		usage
		exit 1
		;;
esac