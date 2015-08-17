#include <stdio.h>
#include <unistd.h>
#include <stdlib.h>
#include <sys/wait.h> 

int main(int argc, char **argv){
	int i = 0;
	for(; i < 2; i++){
		pid_t fpid = fork();
		pid_t pid = getpid();
		if (fpid == 0){
			printf("i am a child process, my pid is %d and my parent's pid is %d.\n\t" 
				"I cannot fork myself, i will terminate after sleeping one second.\n", pid, getppid());
			sleep(1);
			_exit(EXIT_SUCCESS);
			//sleep(2);
		}
		else if (pid > 0){
			printf("i am the parent process, my pid is %d and just forked the child process %d\n", pid, fpid);
			sleep(2);
			//join();
			int status;
			(void)waitpid(pid, &status, 0);
			//printf("child done.");
		}
	}
	exit(EXIT_SUCCESS);
}
