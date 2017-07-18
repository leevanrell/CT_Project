#!/usr/bin/env Rscript
options(warn=-1) # disables those pesky warnings
args <- commandArgs(TRUE)
LOCATION <- args[1]
for (i in 2:length(args)) {
	if (args[i] == '$') {
		setwd(as.character(args[i + 1]))
		break
	} else {
		LOCATION <- paste(LOCATION, args[i], sep = ' ')
	}
}

library(ggplot2)
library(ggmap)
library(dplyr) # dunno if i'm still using this, filter()?

table_file <- read.csv('table.csv' , sep = ',', colClasses=c('character')) 
table_file$rxl <- as.numeric(table_file$rxl)
table_file$lat <- as.numeric(table_file$lat)
table_file$lon <- as.numeric(table_file$lon)
table_frame = data.frame(table_file$Cell_ID, table_file$rxl, table_file$lon, table_file$lat)
colnames(table_frame) = c('Cell_ID', 'rxl', 'lon', 'lat') 

towers_file <- read.csv('towers.csv', sep = ',', colClasses=c('character')) 
towers_file$lat <- as.numeric(towers_file$lat)
towers_file$lon <- as.numeric(towers_file$lon)
towers_frame = data.frame(towers_file$Cell_ID, towers_file$lon, towers_file$lat)
colnames(towers_frame) = c('Cell_ID', 'lon', 'lat')

auburn_map <- get_map(location = LOCATION, zoom = 12, scale = 'auto') # Loads map
# Creates map w/ all data points
map <- ggmap(auburn_map, extent = 'device') + geom_point(data=towers_frame, aes(lon, lat), size=3, col='blue') + geom_point(data = table_frame, aes(x = lon, y = lat), alpha = 1, size = 2) 
png(filename = 'all.png', width=960, height=960)
print(map)
dev.off()

auburn_map <- get_map(location = LOCATION, zoom = 14, scale = 'auto') # Loads map (changes zoom)
#towers <- unique(c(as.character(table_frame$Cell_ID)))
towers <- as.character(towers_frame$Cell_ID)
# loops through each tower and creates a png for each
for (tower in towers){
	filtered_table <- filter(table_frame, table_frame$Cell_ID == tower)
	filtered_towers <- filter(towers_frame, towers_frame$Cell_ID == tower)
	one <- ggmap(auburn_map, extent = 'device') + geom_point(data=filtered_towers, aes(lon, lat), size=3, col='blue')
	one <- one + geom_point(data = filtered_table, aes(x = lon, y = lat), alpha = 1, size = 2) 
	one <- one + geom_tile(data = table_frame, aes(x = lon, y = lat, alpha = rxl), fill = 'red')
	one <- one + theme(axis.title.y = element_blank(), axis.title.x = element_blank())
	#one <- one + geom_tile(data = filtered_table, aes(x = lon , y = lat, z = rxl, fill = rxl), alpha = .8)
	#one <- one + stat_contour(data = filtered_table, aes(x = lon, y = lat, z = rxl)) 
	#one <- one + ggtitle('Place Holder') + xlab('Longitude') + ylab('Latitude')
	#one <- one + scale_fill_continous(name = 'receive level', low 'green', high = 'red')
	#one <- one +   theme(plot.title = element_text(size = 25, face = "bold"), legend.title = element_text(size = 15), axis.text = element_text(size = 15), axis.title.x = element_text(size = 20, vjust = -0.5), axis.title.y = element_text(size = 20, vjust = 0.2), legend.text = element_text(size = 10)) + coord_map()
	png(filename = sprintf('%s.png', tower), width=960, height=960)
	print(one)
	dev.off()
}


clea