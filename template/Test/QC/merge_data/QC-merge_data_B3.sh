echo ==========start at : `date +"%Y-%m-%d %H:%M:%S"` ========== &&\
/mingw64/bin/make -f D:\message_about_myself\program-project\STPG\STPG_public\template/Modules/QC.mk outdir=D:\message_about_myself\program-project\STPG\STPG_public\template\Test MainModule=QC ChildModule=merge_data sample_id=B3 merge_data &&\
echo ==========end at : `date +"%Y-%m-%d %H:%M:%S"` ========== &&\
echo finished 1>&2 &&\
echo finished >$0.finished