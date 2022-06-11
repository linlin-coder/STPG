echo ==========start at : `date +"%Y-%m-%d %H:%M:%S"` ========== &&\
/mingw64/bin/make -f D:\message_about_myself\program-project\STPG\STPG_public\template/Modules/QC.mk sample_id=A2 outdir=D:\message_about_myself\program-project\STPG\STPG_public\template\Test MainModule=QC ChildModule=qc qc File1=D:\message_about_myself\program-project\STPG\STPG_public\template\Test/QC/merge_data/A1_table1.xls &&\
echo yes && whoami &&\
echo ==========end at : `date +"%Y-%m-%d %H:%M:%S"` ========== &&\
echo finished 1>&2 &&\
echo finished >$0.finished