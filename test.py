def main():
	str = "0,1,,233,1"
	str = str.split(",")
	print str[0]
	print str[1]
	print str[2]
	print str[3]
	print str[4]
	print len(str[2]) == 0
	print len(str[3]) == 3

if __name__ == "__main__":
	main()